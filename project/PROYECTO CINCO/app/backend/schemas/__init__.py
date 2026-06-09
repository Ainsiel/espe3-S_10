"""
schemas/__init__.py
"""
from .common import DataResponse, ErrorResponse, Meta, PaginationParams
from .auth import TokenResponse, LoginRequest, UserCreate, UserRead
from .customers import CustomerCreate, CustomerUpdate, CustomerRead, ContactCreate, ContactRead
from .products import ProductCreate, ProductUpdate, ProductRead, CategoryCreate, CategoryRead, UnitCreate, UnitRead
from .inventory import WarehouseCreate, WarehouseRead, StockRead, MovementCreate, MovementRead, AdjustmentCreate, TransferCreate
from .sales import SalesOrderCreate, SalesOrderRead, SalesOrderUpdate, QuotationCreate, QuotationRead, DispatchCreate, ReturnCreate, ReturnRead
from .purchases import SupplierCreate, SupplierRead, PurchaseOrderCreate, PurchaseOrderRead, GoodsReceiptCreate
from .production import BOMCreate, BOMRead, ProductionOrderCreate, ProductionOrderRead
from .billing import InvoiceCreate, InvoiceRead, PaymentCreate, PaymentRead, CreditNoteCreate, DebitNoteCreate
from .alerts import AlertCreate, AlertRead, AlertUpdate
