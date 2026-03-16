from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.host import Host
from ..schemas.host import DeployKeyRequest, HostCreate, HostRead, HostUpdate
from ..services.ssh_manager import deploy_key, list_ssh_keys

router = APIRouter(prefix="/api/hosts", tags=["hosts"])


@router.get("", response_model=list[HostRead])
def list_hosts(db: Session = Depends(get_db)):
    return db.query(Host).all()


@router.post("", response_model=HostRead, status_code=201)
def create_host(payload: HostCreate, db: Session = Depends(get_db)):
    if db.query(Host).filter(Host.name == payload.name).first():
        raise HTTPException(409, "Host name already exists")
    host = Host(**payload.model_dump())
    db.add(host)
    db.commit()
    db.refresh(host)
    return host


@router.get("/ssh-keys")
def get_ssh_keys():
    return list_ssh_keys()


@router.get("/{host_id}", response_model=HostRead)
def get_host(host_id: int, db: Session = Depends(get_db)):
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    return host


@router.put("/{host_id}", response_model=HostRead)
def update_host(host_id: int, payload: HostUpdate, db: Session = Depends(get_db)):
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(host, k, v)
    db.commit()
    db.refresh(host)
    return host


@router.delete("/{host_id}", status_code=204)
def delete_host(host_id: int, db: Session = Depends(get_db)):
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    db.delete(host)
    db.commit()


@router.post("/{host_id}/deploy-key")
def deploy_host_key(
    host_id: int, payload: DeployKeyRequest, db: Session = Depends(get_db)
):
    host = db.get(Host, host_id)
    if not host:
        raise HTTPException(404, "Host not found")
    try:
        deploy_key(host.hostname, host.port, host.username, payload.password)
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"detail": "Key deployed successfully"}
