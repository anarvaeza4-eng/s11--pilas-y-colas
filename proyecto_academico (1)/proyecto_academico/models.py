from datetime import date

# =====================================================================
# CLASE BASE: lo que los tres modelos comparten (NO se toca)
# =====================================================================
class ModeloBase:
    """Padre de todos los modelos. Guarda el id y define el comportamiento común."""

    def __init__(self, id_registro):
        self.id = int(id_registro)

    # ---- ÚNICO MÉTODO DE CLASE DEL PROYECTO ----
    @classmethod
    def desde_diccionario(cls, datos):
        """Diccionario -> objeto. Escrito UNA vez y usado por todos los modelos.
        cls es la clase que llamó: Estudiante, Materia o Matricula."""
        datos = dict(datos)                 # copia, para no tocar el original
        id_registro = datos.pop("id")       # saco el id
        return cls(id_registro, **datos)    # el resto son los campos del modelo

    def a_diccionario(self):
        return {"id": self.id}

    def etiqueta(self):
        # POLIMORFISMO: cada hijo la reescribe a su manera
        return f"registro {self.id}"

    def __str__(self):
        return f"[{self.id}] {self.etiqueta()}"

# =====================================================================
# PERSONA (ya estaba escrita, se reutiliza)
# =====================================================================
class Persona(ModeloBase):
    """Todo lo que tiene una persona del sistema."""

    def __init__(self, id_registro, nombre, apellido, email):
        super().__init__(id_registro)
        self.nombre = nombre
        self.apellido = apellido
        self.email = email

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["nombre"] = self.nombre
        datos["apellido"] = self.apellido
        datos["email"] = self.email
        return datos

    def etiqueta(self):
        return self.nombre_completo()

# =====================================================================
# ESTUDIANTE  (equivale a Cliente)
# =====================================================================
class Estudiante(Persona):
    """Estudiante ES UNA Persona, con carnet y carrera."""

    def __init__(self, id_registro, nombre, apellido, email, carnet="", carrera=""):
        super().__init__(id_registro, nombre, apellido, email)
        self.carnet = carnet
        self.carrera = carrera

    def a_diccionario(self):
        datos = super().a_diccionario()      # id + nombre + apellido + email
        datos["carnet"] = self.carnet
        datos["carrera"] = self.carrera
        return datos

    def etiqueta(self):
        # Sobrescribe y EXTIENDE la del padre
        return f"{super().etiqueta()} · {self.carnet} · {self.carrera or 'sin carrera'}"

# =====================================================================
# MATERIA  (equivale a Producto): aquí vive TODO lo estático
# =====================================================================
class Materia(ModeloBase):
    """Materia ES UN ModeloBase."""

    # ATRIBUTOS ESTÁTICOS: una sola vez para todo el programa (política de la institución)
    CUPOS_MAXIMOS = 30
    NOTA_APROBACION = 14

    def __init__(self, id_registro, nombre, codigo, creditos=0, cupos=0):
        super().__init__(id_registro)
        self.nombre = nombre
        self.codigo = codigo
        self.creditos = int(creditos)
        self.cupos = int(cupos)

    # MÉTODO ESTÁTICO: la regla "entre 0 y 20" no depende de ninguna materia concreta
    @staticmethod
    def es_nota_valida(valor):
        try:
            numero = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            return False
        return 0 <= numero <= 20

    # MÉTODOS DE INSTANCIA: usan los cupos de ESTA materia
    def hay_cupo(self):
        return self.cupos > 0

    def ocupar_cupo(self):
        self.cupos -= 1

    def liberar_cupo(self):
        self.cupos += 1

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["nombre"] = self.nombre
        datos["codigo"] = self.codigo
        datos["creditos"] = self.creditos
        datos["cupos"] = self.cupos
        return datos

    def etiqueta(self):
        alerta = "" if self.hay_cupo() else " ⚠ sin cupo"
        return f"{self.codigo} · {self.nombre} · {self.creditos} créditos · cupos {self.cupos}{alerta}"

# =====================================================================
# MATRICULA  (equivale a Venta): une estudiante y materia por id
# =====================================================================
class Matricula(ModeloBase):
    """Una matrícula: un estudiante, una materia, un periodo y (luego) una nota."""

    def __init__(self, id_registro, estudiante_id, materia_id, periodo,
                 nota=None, fecha=""):
        super().__init__(id_registro)
        self.estudiante_id = int(estudiante_id)
        self.materia_id = int(materia_id)
        self.periodo = periodo
        # None = todavía sin nota (se guarda como null en el JSON)
        self.nota = float(nota) if nota is not None else None
        self.fecha = fecha or date.today().isoformat()

    # Se CALCULAN, no se guardan: así nunca quedan desactualizados
    def esta_aprobada(self):
        return self.nota is not None and self.nota >= Materia.NOTA_APROBACION

    def estado(self):
        if self.nota is None:
            return "Pendiente"
        return "Aprobado" if self.esta_aprobada() else "Reprobado"

    def a_diccionario(self):
        datos = super().a_diccionario()
        datos["estudiante_id"] = self.estudiante_id
        datos["materia_id"] = self.materia_id
        datos["periodo"] = self.periodo
        datos["nota"] = self.nota
        datos["fecha"] = self.fecha
        return datos

    def etiqueta(self):
        nota = "sin nota" if self.nota is None else f"nota {self.nota:g}"
        return (f"{self.periodo} · estudiante {self.estudiante_id} · "
                f"materia {self.materia_id} · {nota} · {self.estado()}")
