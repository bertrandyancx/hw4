from pydantic import BaseModel, Field


class ProductCard(BaseModel):
    product_id: str
    name: str
    price: float
    description: str
    image_url: str
    available_sizes: list[str] = Field(default_factory=list)


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(ge=0)


class ProductLookup(BaseModel):
    """Authoritative catalogue and inventory facts returned by a database tool."""
    product_id: str
    name: str
    description: str
    price: float = Field(ge=0)
    total_in_stock: int = Field(ge=0)
    stock_by_size: list[SizeStock] = Field(default_factory=list)


class ChatReply(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    token: str | None = None
    page_context: str | None = Field(default=None, max_length=500)


class ChatContext(BaseModel):
    user: dict | None = None
    page_context: str | None = None
    recent_messages: list[dict] = Field(default_factory=list, max_length=8)
