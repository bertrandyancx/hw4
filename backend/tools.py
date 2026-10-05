import json
import sqlite3
from pathlib import Path

from pydantic_ai import RunContext

from models import ChatContext, ProductCard, ProductLookup, SizeStock
from audit import record

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"


def search_products(_ctx: RunContext[ChatContext], query: str) -> list[ProductCard]:
    """Search the local catalogue and return factual product cards for the shopper."""
    terms = [term.lower().rstrip("s") for term in query.split() if len(term) > 2]
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        matches = []
        for row in rows:
            searchable = " ".join((row["name"], row["garment_type"], row["description"], row["colors"], row["search_tags"])).lower()
            score = sum(searchable.count(term) for term in terms)
            if not terms or score > 0:
                stock = connection.execute("SELECT size FROM inventory WHERE product_id = ? AND quantity > 0 ORDER BY id", (row["product_id"],)).fetchall()
                matches.append((score, ProductCard(product_id=row["product_id"], name=row["name"], price=row["price"], description=row["description"], image_url=f"/images/{row['image_file_path']}", available_sizes=[item["size"] for item in stock])))
    result = [product for _, product in sorted(matches, key=lambda item: (-item[0], item[1].name))[:6]]
    record("search_products", f"query={query!r}", f"matches={len(result)}")
    return result


def lookup_product_information(_ctx: RunContext[ChatContext], product_id: str) -> ProductLookup | None:
    """Look up authoritative description, price, total stock, and stock by size for one product."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        product = connection.execute("SELECT product_id, name, description, price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if product is None:
            record("lookup_product_information", f"product_id={product_id!r}", "not found")
            return None
        rows = connection.execute("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)).fetchall()
    stock = [SizeStock(size=row["size"], quantity=row["quantity"]) for row in rows]
    result = ProductLookup(product_id=product["product_id"], name=product["name"], description=product["description"], price=product["price"], total_in_stock=sum(item.quantity for item in stock), stock_by_size=stock)
    record("lookup_product_information", f"product_id={product_id!r}", f"price={result.price}, total={result.total_in_stock}")
    return result


def get_product_stock(_ctx: RunContext[ChatContext], product_id: str) -> list[SizeStock]:
    """Read exact per-size quantities for a catalogue product from the local database."""
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)).fetchall()
    result = [SizeStock(size=size, quantity=quantity) for size, quantity in rows]
    record("get_product_stock", f"product_id={product_id!r}", f"sizes={len(result)}")
    return result


def get_customer_context(ctx: RunContext[ChatContext]) -> dict:
    """Return the safe customer and page context supplied with this chat request."""
    result = {"customer": ctx.deps.user, "page_context": ctx.deps.page_context}
    record("get_customer_context", "no private args", f"logged_in={ctx.deps.user is not None}")
    return result
