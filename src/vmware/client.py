"""
VMware vSphere vCenter & ESXi Client.
Manages REST and SOAP API sessions with VMware hypervisors, handling authentication tokens,
connection pooling, and automatic failover to local enterprise emulation.
"""

from typing import Dict, List, Optional, Any
import logging
import time
import httpx

from src.vmware.config import VMwareConfig

logger = logging.getLogger("aegispath.vmware.client")


class VMwareClient:
    """
    Client for interacting with VMware vCenter Server and standalone ESXi hosts.
    Supports session-based REST API authentication and automated emulation fallback.
    """

    def __init__(self, config: Optional[VMwareConfig] = None):
        self.config = config or VMwareConfig.from_env()
        self.session_id: Optional[str] = None
        self.is_connected: bool = False
        self.is_emulated: bool = False
        self.base_url = f"https://{self.config.host}:{self.config.port}/api"
        self._http_client: Optional[httpx.Client] = None

    def connect(self) -> bool:
        """
        Authenticates against VMware vCenter REST endpoint.
        Falls back to enterprise emulation if real vCenter host is unreachable.
        """
        if self.is_connected:
            return True

        try:
            self._http_client = httpx.Client(
                verify=self.config.verify_ssl,
                timeout=float(self.config.connection_timeout_seconds),
            )
            # vSphere REST Authentication: POST /api/session
            auth_url = f"{self.base_url}/session"
            resp = self._http_client.post(
                auth_url,
                auth=(self.config.username, self.config.password),
            )
            if resp.status_code in (200, 201):
                self.session_id = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text.strip('"')
                self._http_client.headers.update({"vmware-api-session-id": self.session_id})
                self.is_connected = True
                self.is_emulated = False
                logger.info(f"Connected to live VMware vCenter at {self.config.host}")
                return True
            else:
                logger.warning(f"vCenter auth returned {resp.status_code}. Fallback triggered.")
                return self._trigger_fallback()
        except Exception as e:
            logger.info(f"Live vCenter unreachable ({e}). Using enterprise hypervisor emulation.")
            return self._trigger_fallback()

    def _trigger_fallback(self) -> bool:
        """Enables high-fidelity hypervisor emulation when physical vCenter is absent."""
        if self.config.enable_emulation_fallback:
            self.is_connected = True
            self.is_emulated = True
            self.session_id = "emulated-vsphere-session-token-v8"
            return True
        self.is_connected = False
        return False

    def disconnect(self):
        """Terminates vSphere session and frees HTTP client resources."""
        if self._http_client and self.session_id and not self.is_emulated:
            try:
                self._http_client.delete(f"{self.base_url}/session")
            except Exception:
                pass
        if self._http_client:
            self._http_client.close()
        self._http_client = None
        self.session_id = None
        self.is_connected = False
        self.is_emulated = False

    def get_status(self) -> Dict[str, Any]:
        """Returns client health and connectivity metrics."""
        return {
            "connected": self.is_connected,
            "emulated": self.is_emulated,
            "host": self.config.host,
            "port": self.config.port,
            "username": self.config.username,
            "datacenter": self.config.datacenter,
            "cluster": self.config.cluster,
            "session_active": self.session_id is not None,
        }
