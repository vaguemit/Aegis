"""
VMware Integration Configuration and Credentials Resolver.
Loads settings from environment variables or YAML configuration files with security defaults.
"""

from dataclasses import dataclass, field
import os
from typing import Optional
import yaml


@dataclass
class VMwareConfig:
    """Connection parameters and operational policies for VMware vCenter / ESXi."""
    host: str = "vcenter.corp.internal"
    port: int = 443
    username: str = "administrator@vsphere.local"
    password: str = "VMwareSecretPass!2026"
    verify_ssl: bool = False
    datacenter: str = "Datacenter-Core"
    cluster: str = "Cluster-Production"
    quarantine_portgroup: str = "Quarantine_VLAN_999"
    quarantine_vlan: int = 999
    enable_emulation_fallback: bool = True
    connection_timeout_seconds: int = 15

    @classmethod
    def from_env(cls) -> "VMwareConfig":
        """Loads configuration overrides from system environment variables."""
        return cls(
            host=os.getenv("VCENTER_HOST", "vcenter.corp.internal"),
            port=int(os.getenv("VCENTER_PORT", "443")),
            username=os.getenv("VCENTER_USERNAME", "administrator@vsphere.local"),
            password=os.getenv("VCENTER_PASSWORD", "VMwareSecretPass!2026"),
            verify_ssl=os.getenv("VCENTER_VERIFY_SSL", "false").lower() in ("true", "1", "yes"),
            datacenter=os.getenv("VCENTER_DATACENTER", "Datacenter-Core"),
            cluster=os.getenv("VCENTER_CLUSTER", "Cluster-Production"),
            quarantine_portgroup=os.getenv("VCENTER_QUARANTINE_PG", "Quarantine_VLAN_999"),
            quarantine_vlan=int(os.getenv("VCENTER_QUARANTINE_VLAN", "999")),
            enable_emulation_fallback=os.getenv("VCENTER_EMULATION_FALLBACK", "true").lower() in ("true", "1", "yes"),
        )

    @classmethod
    def from_yaml(cls, file_path: str) -> "VMwareConfig":
        """Loads configuration from YAML file, falling back to environment defaults."""
        if not os.path.exists(file_path):
            return cls.from_env()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            cfg = data.get("vmware", {})
            return cls(
                host=cfg.get("host", "vcenter.corp.internal"),
                port=cfg.get("port", 443),
                username=cfg.get("username", "administrator@vsphere.local"),
                password=cfg.get("password", "VMwareSecretPass!2026"),
                verify_ssl=cfg.get("verify_ssl", False),
                datacenter=cfg.get("datacenter", "Datacenter-Core"),
                cluster=cfg.get("cluster", "Cluster-Production"),
                quarantine_portgroup=cfg.get("quarantine_portgroup", "Quarantine_VLAN_999"),
                quarantine_vlan=cfg.get("quarantine_vlan", 999),
                enable_emulation_fallback=cfg.get("enable_emulation_fallback", True),
            )
        except Exception:
            return cls.from_env()
