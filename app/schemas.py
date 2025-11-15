from pydantic import BaseModel, ConfigDict


class PurchaseBase(BaseModel):
    number: str
    customer: str
    subject: str
    amount: str
    dates: str
    status: str
    link: str


class PurchaseCreate(PurchaseBase):
    pass


class PurchaseResponse(PurchaseBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
