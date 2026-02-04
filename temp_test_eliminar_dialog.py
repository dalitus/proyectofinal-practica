from proyectofinal.pages.adnmin_shouder_page import AdminState
s = AdminState()
print('initial id:', s.producto_id_a_eliminar)
s.set_producto_a_eliminar(42)
print('after set:', s.producto_id_a_eliminar)
# Simulate cancel click
s.set_producto_a_eliminar(0)
print('after cancel:', s.producto_id_a_eliminar)
# Simulate confirm path: set then confirm
s.set_producto_a_eliminar(99)
print('before confirm:', s.producto_id_a_eliminar)
try:
    s.confirmar_eliminacion()
except Exception as e:
    print('confirm raised (may attempt DB op):', e)
print('after confirm (should be 0):', s.producto_id_a_eliminar)
