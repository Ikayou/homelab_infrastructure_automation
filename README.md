# HomeLab Infrastructure & Automation
Ein Projekt zur Implementierung einer privaten Cloud-Umgebung auf Basis von **AlmaLinux unter Hyper-V**, kombiniert mit Docker-Container-Orchestrierung und **Ansible-Automatisierung**.

## Überblick
Dieses Projekt demonstriert den Aufbau einer skalierbaren Infrastruktur, die Sichtbarkeit (NetBox), Monitoring (Zabbix), Management (Portainer/Homepage) und Automatisierung (Ansible) vereint. Ein besonderes Highlight ist die Kopplung von Ansible mit NetBox als "Source of Truth".

## Infrastruktur-Stack
### 1. Basis-Infrastruktur
* **Hypervisor:** Hyper-V
* **Betriebssystem:** AlmaLinux 9.x (installiert in einer VM)
* **Container-Laufzeit:** Docker & Docker Compose

### 2. Services (Docker-Container)
| Service | Rolle | Besonderheit |
| :--- | :--- | :--- |
| **Traefik** | Reverse Proxy | Automatisches Routing über FQDNs und SSL-Terminierung |
| **Portainer** | Container-Management | Visualisierung und Management von Stacks und Containern |
| **Homepage** | Dashboard | Zentraler Überblick über Ressourcen, Versionen und API-Status |
| **NetBox** | IPAM / DCIM | Zentrale Verwaltung aller Netzwerk- und Server-Assets (Source of Truth) |
| **Zabbix** | Monitoring | Echtzeit-Überwachung der Systemressourcen |
| **Redmine** | Projektmanagement | Dokumentation von Workflows und Wissensdatenbank |

### 3. Automatisierung (Infrastructure as Code)
Das Herzstück der Automatisierung ist die **Ansible-Integration**:
* **Dynamisches Inventar:** Ansible nutzt die NetBox-API, um Server-Listen dynamisch zu generieren.
* **One-Command-Maintenance:** Mit nur einem Befehl können alle in NetBox registrierten Server gleichzeitig aktualisiert oder konfiguriert werden.

---

## Funktionen & Highlights
* **Service Discovery:** Automatische Erkennung neuer Container durch Traefik-Labels.
* **Zentrales Dashboard:** Homepage aggregiert Daten direkt aus dem Docker-Socket, um CPU, RAM und Speicherplatz anzuzeigen.
* **Automatisierte Wartung:** Effizientes Server-Management durch die Verbindung von NetBox und Ansible-Playbooks.

## Installation & Setup
*(Hier könntest du später kurz beschreiben, wie man z.B. das Ansible-Playbook startet oder die Docker-Stacks ausrollt)*

```bash
# Beispiel: Ausführen des Wartungs-Playbooks
ansible-playbook -i netbox_inv.yml update_servers.yml
```

---
