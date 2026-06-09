"""
routers/customers.py — CRUD de clientes y contactos.
Endpoints 16-27: GET/POST/PATCH/DELETE /customers, /contacts, /credit, /statement
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.auth import User, AuditLog
from models.customers import Customer, CustomerContact
from schemas.customers import (CustomerCreate, CustomerUpdate, CustomerRead,
                                ContactCreate, ContactRead, CreditUpdate)
from dependencies import get_current_user, require_permission

router = APIRouter(prefix="/api/v1/customers", tags=["Clientes"])


@router.get("", summary="Listar clientes")
def list_customers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.read")),
):
    """P-04: Listado de clientes con filtros y paginación. RNF-03: p95 < 800ms."""
    q = db.query(Customer).filter(Customer.company_id == current_user.company_id)
    if search:
        q = q.filter(
            Customer.legal_name.ilike(f"%{search}%") |
            Customer.tax_id.ilike(f"%{search}%") |
            Customer.billing_email.ilike(f"%{search}%")
        )
    if status:
        q = q.filter(Customer.status == status)
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [CustomerRead.model_validate(c) for c in items],
            "meta": {"total": total, "page": page, "page_size": page_size}}


@router.post("", response_model=CustomerRead, status_code=201, summary="Crear cliente")
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.create")),
):
    """UC-CLI-01: Registrar cliente. V036-V038: Razón social, doc tributario único."""
    # V038: Documento tributario único por empresa
    existing = db.query(Customer).filter(
        Customer.company_id == current_user.company_id,
        Customer.tax_id == payload.tax_id.strip()
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Documento tributario ya registrado")

    customer = Customer(**payload.model_dump(), created_by=current_user.id)
    db.add(customer)
    db.flush()
    db.add(AuditLog(actor_id=current_user.id, entity="customers",
                    entity_id=str(customer.id), action="create",
                    after_data=payload.model_dump(mode="json")))
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerRead, summary="Obtener cliente")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.read")),
):
    """P-06: Detalle de cliente."""
    c = db.query(Customer).filter(Customer.id == customer_id,
                                   Customer.company_id == current_user.company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return c


@router.patch("/{customer_id}", response_model=CustomerRead, summary="Actualizar cliente")
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.update")),
):
    """UC-CLI-02: Editar cliente. No permite editar clientes eliminados."""
    c = db.query(Customer).filter(Customer.id == customer_id,
                                   Customer.company_id == current_user.company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if c.status == "inactive":
        raise HTTPException(status_code=409, detail="No se puede editar cliente inactivo")

    before = CustomerRead.model_validate(c).model_dump(mode="json")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.add(AuditLog(actor_id=current_user.id, entity="customers",
                    entity_id=str(c.id), action="update",
                    before_data=before, after_data=payload.model_dump(mode="json")))
    db.commit()
    db.refresh(c)
    return c


@router.delete("/{customer_id}", summary="Inactivar cliente")
def inactivate_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.delete")),
):
    """UC-CLI-05: Eliminación lógica (soft delete). RN-4: No físico si tiene historial."""
    c = db.query(Customer).filter(Customer.id == customer_id,
                                   Customer.company_id == current_user.company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    c.status = "inactive"
    db.add(AuditLog(actor_id=current_user.id, entity="customers",
                    entity_id=str(c.id), action="inactivate"))
    db.commit()
    return {"message": "Cliente inactivado"}


# --- Contactos ---
@router.get("/{customer_id}/contacts", summary="Listar contactos")
def list_contacts(customer_id: int, db: Session = Depends(get_db),
                  current_user: User = Depends(require_permission("customers.read"))):
    contacts = db.query(CustomerContact).filter(CustomerContact.customer_id == customer_id).all()
    return {"data": [ContactRead.model_validate(c) for c in contacts]}


@router.post("/{customer_id}/contacts", response_model=ContactRead, status_code=201, summary="Crear contacto")
def create_contact(
    customer_id: int,
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.update")),
):
    """V051: Solo un contacto principal por cliente."""
    if payload.is_primary:
        existing_primary = db.query(CustomerContact).filter(
            CustomerContact.customer_id == customer_id,
            CustomerContact.is_primary == True
        ).first()
        if existing_primary:
            existing_primary.is_primary = False
    contact = CustomerContact(customer_id=customer_id, **payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.patch("/customer-contacts/{contact_id}", response_model=ContactRead, summary="Actualizar contacto")
def update_contact(
    contact_id: int,
    payload: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.update")),
):
    contact = db.query(CustomerContact).filter(CustomerContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(contact, field, value)
    db.commit()
    db.refresh(contact)
    return contact


# --- Crédito ---
@router.get("/{customer_id}/credit", summary="Consultar crédito")
def get_credit(customer_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(require_permission("customers.credit.manage"))):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"data": {"credit_limit": c.credit_limit, "credit_status": c.credit_status,
                     "payment_term_days": c.payment_term_days,
                     "credit_block_reason": c.credit_block_reason}}


@router.patch("/{customer_id}/credit", summary="Actualizar crédito")
def update_credit(
    customer_id: int,
    payload: CreditUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("customers.credit.manage")),
):
    """UC-CLI-04: Gestionar crédito. V046-V048."""
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    db.add(AuditLog(actor_id=current_user.id, entity="customers",
                    entity_id=str(c.id), action="update_credit",
                    after_data=payload.model_dump(mode="json")))
    db.commit()
    return {"message": "Crédito actualizado"}
