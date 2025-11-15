from pydantic import BaseModel


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

    class Config:
        orm_mode = True
