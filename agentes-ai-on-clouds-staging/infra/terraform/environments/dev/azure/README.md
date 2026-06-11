# Azure AKS — dev

Copiar estructura desde `../aws/` y adaptar:

- `backend.tf.example` → `backend "azurerm" { ... }`
- Provider `azurerm` ~> 3.x
- Módulo platform → submódulo AKS + VNet
