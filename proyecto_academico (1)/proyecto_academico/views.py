from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido

# TUPLA: campos fijos que nunca cambian durante la ejecución; por eso no son lista.
CAMPOS_OBLIGATORIOS_ESTUDIANTE = ("nombre", "apellido", "email", "carnet")
CAMPOS_BUSCABLES_ESTUDIANTE = ("nombre", "apellido", "email", "carnet", "carrera")
CAMPOS_BUSCABLES_MATERIA = ("nombre", "codigo")

# =====================================================================
# CLASE BASE (ABSTRACTA): solo dice QUÉ métodos debe tener todo controlador
# =====================================================================
class CrudBase(ABC):

    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass

# =====================================================================
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)

        # LISTA de objetos: la colección que crece y se recorre
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Estudiante.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for estudiante in self.lista:
            datos.append(estudiante.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Al crear deben venir los cuatro obligatorios; al actualizar,
        # solo se revisa que lo que cambia no quede vacío.
        for campo in CAMPOS_OBLIGATORIOS_ESTUDIANTE:
            if id_actual is None or campo in datos:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            # CONJUNTO de emails de los OTROS estudiantes: "in" es instantáneo
            usados = {e.email for e in self.lista if e.id != id_actual}
            if email in usados:
                return "Ese email ya está registrado"

        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            # CONJUNTO de carnets ya usados: comparar sin importar mayúsculas
            carnets = {e.carnet.upper() for e in self.lista if e.id != id_actual}
            if carnet in carnets:
                return "Ese carnet ya está registrado"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados

        for estudiante in self.lista:
            for campo in CAMPOS_BUSCABLES_ESTUDIANTE:
                if texto in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break          # ya coincidió: no repetirlo por otro campo
        return encontrados

    def siguiente(self):
        mayor = 0
        for estudiante in self.lista:
            if estudiante.id > mayor:
                mayor = estudiante.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        estudiante = Estudiante(self.siguiente(),
                                str(datos["nombre"]).strip().title(),
                                str(datos["apellido"]).strip().title(),
                                str(datos["email"]).strip().lower(),
                                str(datos["carnet"]).strip().upper(),
                                str(datos.get("carrera", "")).strip().title())
        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que no existen en un estudiante
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_estudiante)
        if error:
            return False, error

        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            setattr(estudiante, campo, valor)

        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"

        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # --- propio de estudiantes ---
    def carreras(self):
        """CONJUNTO de carreras: sin repetidos. sorted() lo devuelve como lista."""
        return sorted({e.carrera for e in self.lista if e.carrera != ""})

# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Materia.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for materia in self.lista:
            datos.append(materia.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        for campo in ("nombre", "codigo", "creditos"):
            if id_actual is None or campo in datos:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            # CONJUNTO de códigos de las OTRAS materias
            codigos = {m.codigo.upper() for m in self.lista if m.id != id_actual}
            if codigo in codigos:
                return f"Ya existe una materia con el código {codigo}"

        if "creditos" in datos:
            creditos = str(datos["creditos"]).strip()
            if not creditos.isdigit() or not 1 <= int(creditos) <= 10:
                return "Los créditos deben ser un entero entre 1 y 10"

        cupos = str(datos.get("cupos", "")).strip()
        if cupos != "":
            # CUPOS_MAXIMOS es el atributo ESTÁTICO de Materia
            if not cupos.isdigit() or int(cupos) > Materia.CUPOS_MAXIMOS:
                return f"Los cupos deben ser un entero entre 0 y {Materia.CUPOS_MAXIMOS}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontradas = []
        if texto == "":
            return encontradas

        for materia in self.lista:
            for campo in CAMPOS_BUSCABLES_MATERIA:
                if texto in str(getattr(materia, campo)).lower():
                    encontradas.append(materia)
                    break
        return encontradas

    def siguiente(self):
        mayor = 0
        for materia in self.lista:
            if materia.id > mayor:
                mayor = materia.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        cupos = str(datos.get("cupos", "")).strip()      # vacío = 0 cupos
        materia = Materia(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["codigo"]).strip().upper(),
                          int(str(datos["creditos"]).strip()),
                          int(cupos) if cupos != "" else 0)
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"

        desconocidos = set(datos) - {"nombre", "codigo", "creditos", "cupos"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        error = self.validar(datos, id_materia)
        if error:
            return False, error

        if "nombre" in datos:
            materia.nombre = str(datos["nombre"]).strip().title()
        if "codigo" in datos:
            materia.codigo = str(datos["codigo"]).strip().upper()
        if "creditos" in datos:
            materia.creditos = int(datos["creditos"])
        if "cupos" in datos:
            materia.cupos = int(datos["cupos"])

        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"

        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    # --- propio de materias ---
    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo

# =====================================================================
# CONTROLADOR DE MATRÍCULAS
# =====================================================================
class MatriculaController(CrudBase):

    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        # La matrícula USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py (así el cupo ya queda actualizado).
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Matricula.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for matricula in self.lista:
            datos.append(matricula.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"

        periodo = str(datos.get("periodo", "")).strip()
        if periodo == "":
            return "El periodo es obligatorio (ej. 2026-1)"

        # CONJUNTO de ids existentes: preguntar si el estudiante existe es instantáneo
        ids_estudiantes = {e.id for e in self.estudiantes.leer()}
        if estudiante_id not in ids_estudiantes:
            return f"No existe un estudiante con id {estudiante_id}"

        materia = self.materias.obtener(materia_id)
        if materia is None:
            return f"No existe una materia con id {materia_id}"
        if not materia.hay_cupo():
            return f"No hay cupo disponible en {materia.nombre}"

        # CONJUNTO de TUPLAS (estudiante, materia, periodo): las tres cosas se
        # comparan JUNTAS. Una tupla puede estar dentro de un set; una lista no.
        ya_matriculados = {(m.estudiante_id, m.materia_id, m.periodo) for m in self.lista}
        if (estudiante_id, materia_id, periodo) in ya_matriculados:
            return "El estudiante ya está matriculado en esa materia en ese periodo"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    def buscar(self, texto):
        # Las matrículas se buscan por periodo, ej: "2026-1"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas

        for matricula in self.lista:
            if texto in matricula.periodo:
                encontradas.append(matricula)
        return encontradas

    def siguiente(self):
        mayor = 0
        for matricula in self.lista:
            if matricula.id > mayor:
                mayor = matricula.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"estudiante_id": 1, "materia_id": 2, "periodo": "2026-1"}
        error = self.validar(datos)
        if error:
            return False, error

        materia = self.materias.obtener(int(datos["materia_id"]))
        matricula = Matricula(self.siguiente(),
                              int(datos["estudiante_id"]),
                              materia.id,
                              str(datos["periodo"]).strip())

        materia.ocupar_cupo()
        self.materias.guardar()          # guarda el cupo nuevo en materias.json
        self.lista.append(matricula)
        self.guardar()                   # guarda la matrícula en matriculas.json
        return True, f"Matrícula {matricula.id} registrada en {materia.nombre}"

    def actualizar(self, id_matricula, datos):
        # Lo único que cambia en una matrícula ya hecha es la nota
        if set(datos) == {"nota"}:
            return self.registrar_nota(id_matricula, datos["nota"])
        return False, "Solo se puede modificar la nota; para otro cambio retire la matrícula"

    def eliminar(self, id_matricula):
        """Retirar una matrícula: se borra y el cupo vuelve a la materia."""
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"

        materia = self.materias.obtener(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()

        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo devuelto"

    # --- propio de matrículas ---
    def retirar_matricula(self, id_matricula):
        return self.eliminar(id_matricula)

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        # es_nota_valida es el método ESTÁTICO de Materia
        if not Materia.es_nota_valida(nota):
            return False, f"Nota inválida: '{nota}' (debe ser un número entre 0 y 20)"

        matricula.nota = round(float(str(nota).replace(",", ".")), 2)
        self.guardar()
        return True, f"Nota registrada: {matricula.nota:g} ({matricula.estado()})"

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None

        # DICCIONARIOS ÍNDICE {id: objeto}: acceso directo por id, sin recorrer listas
        indice_estudiantes = {e.id: e for e in self.estudiantes.leer()}
        indice_materias = {m.id: m for m in self.materias.leer()}
        estudiante = indice_estudiantes.get(matricula.estudiante_id)
        materia = indice_materias.get(matricula.materia_id)

        nota = "sin nota" if matricula.nota is None else f"{matricula.nota:g}"
        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        if estudiante:
            texto += f"Estudiante: {estudiante.nombre_completo()}   ({estudiante.carnet})\n"
        else:
            texto += "Estudiante: eliminado\n"
        if materia:
            texto += f"Materia   : {materia.nombre}   ({materia.codigo}) · {materia.creditos} créditos\n"
        else:
            texto += "Materia   : eliminada\n"
        texto += "-" * 42 + "\n"
        texto += f"Nota      : {nota}\n"
        texto += f"Estado    : {matricula.estado()}"
        return texto

    def matriculas_por_estudiante(self):
        """DICCIONARIO de LISTAS: {estudiante_id: [matrículas de ese estudiante]}.
        Cada clave guarda VARIOS valores, por eso el valor es una lista."""
        agrupadas = {}
        for matricula in self.lista:
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        """Promedio de las notas ya registradas, o None si todavía no tiene ninguna."""
        propias = self.matriculas_por_estudiante().get(id_estudiante, [])
        notas = [m.nota for m in propias if m.nota is not None]
        if not notas:
            return None
        return round(sum(notas) / len(notas), 2)

    def cantidad_aprobadas(self):
        total = 0
        for matricula in self.lista:
            if matricula.esta_aprobada():
                total += 1
        return total
