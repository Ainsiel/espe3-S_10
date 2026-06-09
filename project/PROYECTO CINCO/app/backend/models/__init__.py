"""
models/__init__.py — Registro de todos los modelos ORM.
Importar aquí para que Alembic y create_tables() los detecte.
"""

from .auth import User, Role, RolePermission, AuditLog
from .customers import Customer, CustomerContact
from .products import Product, ProductCategory, Unit
from .inventory import (
    Warehouse, WarehouseLocation, InventoryStock,
    InventoryMovement, InventoryCount, InventoryCountLine
)
from .sales import (
    Quotation, QuotationLine,
    SalesOrder, SalesOrderLine,
    SalesDispatch, SalesDispatchLine,
    SalesReturn, SalesReturnLine
)
from .purchases import (
    Supplier, SupplierContact,
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceipt, GoodsReceiptLine,
    SupplierInvoice
)
from .production import (
    ProductionBOM, ProductionBOMLine,
    ProductionOrder, ProductionConsumption
)
from .billing import Invoice, InvoiceLine, CreditNote, DebitNote, Payment
from .alerts import Alert, EmailLog, ReportExport, DashboardPreference

__all__ = [
    "User", "Role", "RolePermission", "AuditLog",
    "Customer", "CustomerContact",
    "Product", "ProductCategory", "Unit",
    "Warehouse", "WarehouseLocation", "InventoryStock",
    "InventoryMovement", "InventoryCount", "InventoryCountLine",
    "Quotation", "QuotationLine",
    "SalesOrder", "SalesOrderLine",
    "SalesDispatch", "SalesDispatchLine",
    "SalesReturn", "SalesReturnLine",
    "Supplier", "SupplierContact",
    "PurchaseOrder", "PurchaseOrderLine",
    "GoodsReceipt", "GoodsReceiptLine", "SupplierInvoice",
    "ProductionBOM", "ProductionBOMLine",
    "ProductionOrder", "ProductionConsumption",
    "Invoice", "InvoiceLine", "CreditNote", "DebitNote", "Payment",
    "Alert", "EmailLog", "ReportExport", "DashboardPreference",
]
