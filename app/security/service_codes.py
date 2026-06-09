"""Códigos de servicio (UUID). Cada router exige el suyo; un cliente debe tener
un ``CustomerService`` con ese código para poder llamarlo."""

SERVICE_RCV = "a37be2f6-bf28-4f52-9b5f-99e6c422d112"
SERVICE_DTE = "3c9f2ceb-bfb6-4917-b8e0-26a9c84235ab"
SERVICE_BOOK = "c9f4a1d8-3e72-4b05-af16-7d82b3c0e541"
SERVICE_EXCHANGE = "b1e7d9a2-4c03-4f18-9a6b-2d5e8f0c7a31"

ALL_SERVICES = {
    SERVICE_RCV: "RCV (Registro de Compra y Venta)",
    SERVICE_DTE: "Emisión de DTE",
    SERVICE_BOOK: "Libro de Compras y Ventas (IECV)",
    SERVICE_EXCHANGE: "Acuses de intercambio",
}
