from app.controllers.personal_controller import PersonalController
from app.config.database import test_connection


def probar_personal():
    ok, message = test_connection()
    print("CONEXIÓN:", ok, message)

    if not ok:
        return

    controller = PersonalController()

    data_create = {
        "num_empleado": "TAU0001",
        "id_puesto": 1,
        "id_area": 1,
        "apellido_paterno": "Pérez",
        "apellido_materno": "López",
        "nombres": "Juan Carlos",
        "id_area_res": 1,
        "tc": 3,
        "mail": "juanperez@taurus.com.mx",
        "id_departamento": 1,
        "id_area_res2": 1,
        "perm_fsm": 0,
        "tipo_puesto": 1,
        "activo": True,
        "id_area_res3": None,
    }

    # print("\n--- CREAR ---")
    # ok, message, data = controller.crear_personal(data_create)
    # print(ok, message)
    # print(data)

    # print("\n--- LISTAR ---")
    # ok, message, data = controller.listar_personal()
    # print(ok, message)
    # print(data)

    print("\n--- OBTENER ---")
    ok, message, data = controller.obtener_personal("TAU0001")
    print(ok, message)
    print(data)

    data_update = {
        "num_empleado": "TAU0001",
        "id_puesto": 2,
        "id_area": 1,
        "apellido_paterno": "Pérez",
        "apellido_materno": "García",
        "nombres": "Juan Carlos",
        "id_area_res": 1,
        "tc": 3,
        "mail": "juan.perez@empresa.com",
        "id_departamento": 1,
        "id_area_res2": 1,
        "perm_fsm": 1,
        "tipo_puesto": 2,
        "activo": True,
        "id_area_res3": None,
    }

    print("\n--- ACTUALIZAR ---")
    ok, message, data = controller.actualizar_personal("TAU0001", data_update)
    print(ok, message)
    print(data)

    print("\n--- OBTENER ---")
    ok, message, data = controller.obtener_personal("TAU0001")
    print(ok, message)
    print(data)


    print("\n--- ELIMINAR ---")
    ok, message, data = controller.eliminar_personal("TAU0001")
    print(ok, message)
    print(data)


if __name__ == "__main__":
    probar_personal()