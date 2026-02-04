from proyectofinal.pages.adnmin_shouder_page import AdminState
s = AdminState()
# test abrir/cerrar modal logic
s.abrir_modal_crear()
print('modal_crear_abierto after abrir:', s.modal_crear_abierto)
s.cerrar_modal_crear()
print('modal_crear_abierto after cerrar:', s.modal_crear_abierto)
# abrir editar
s.abrir_modal_editar(123, {'nombre':'x'})
print('modal_editar_abierto after abrir:', s.modal_editar_abierto, 'id_a_editar=', s.producto_id_a_editar)
s.cerrar_modal_editar()
print('modal_editar_abierto after cerrar:', s.modal_editar_abierto, 'id_a_editar=', s.producto_id_a_editar)
