from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import bcrypt
from .models import usuario_repository, lote_repository, rol_repository
from .models.db_singleton import DatabaseSingleton
from .models import usuario_repository, lote_repository, rol_repository, pedido_repository


# --- VISTA DE LOGIN ---
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = usuario_repository.obtener_por_email(email)
            
            if user:
                stored_hash = user['password_hash'].encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    request.session['usuario_id'] = user['id_usuario']
                    request.session['nombre'] = user['nombre']
                    request.session['rol_id'] = user['id_rol']
                    
                    if user['id_rol'] == 1:
                        return redirect('dashboard_acopio')
                    else:
                        return redirect('dashboard_restaurante')
            
            return render(request, 'logistica_app/login.html', {'error': 'Credenciales inválidas.'})
        except Exception as e:
            return render(request, 'logistica_app/login.html', {'error': f'Error de sistema: {str(e)}'})
    
    return render(request, 'logistica_app/login.html')

# --- VISTA DE REGISTRO ---
def registro_view(request):
    roles = rol_repository.obtener_todos()
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo = request.POST.get('correo')
        password = request.POST.get('password')
        rol_id = request.POST.get('rol')
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            usuario_repository.crear_usuario(nombre, correo, hashed, rol_id)
            messages.success(request, "Cuenta creada exitosamente. Inicia sesión.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error al registrar: {str(e)}")
    
    return render(request, 'logistica_app/registro.html', {'roles': roles})

# --- VISTA DE DASHBOARD ACOPIO ---
def dashboard_acopio(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    
    try:
        lotes = lote_repository.obtener_por_usuario(usuario_id)
    except Exception as e:
        print(f"Error cargando lotes del acopio: {e}")
        lotes = []
    
    return render(request, 'logistica_app/dashboard_acopio.html', {
        'nombre': request.session.get('nombre'),
        'lotes': lotes
    })

# --- VISTA DE DASHBOARD RESTAURANTE ---
def dashboard_restaurante(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    try:
        lotes = lote_repository.obtener_disponibles()
    except Exception as e:
        print(f"Error cargando lotes: {e}")
        lotes = []
    
    return render(request, 'logistica_app/dashboard_restaurante.html', {
        'nombre': request.session.get('nombre'),
        'lotes': lotes
    })

# --- VISTA PARA GENERAR REPORTE PDF ---
def generar_reporte_pdf(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    usuario_id = request.session.get('usuario_id')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_inventario_personal.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "RUTA DEL MAR — REPORTE DE INVENTARIO")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 65, "Registro Exclusivo de Acopio")
    p.setLineWidth(1)
    p.line(50, height - 75, width - 50, height - 75)
    
    y = height - 110
    
    try:
        lotes = lote_repository.obtener_por_usuario(usuario_id)
        
        p.setFont("Helvetica-Bold", 11)
        p.drawString(50, y, "Especie")
        p.drawString(250, y, "Disponible (kg)")
        p.drawString(400, y, "Precio/kg")
        y -= 20
        
        p.setFont("Helvetica", 10)
        for lote in lotes:
            if y < 50:
                p.showPage()
                y = height - 50
            p.drawString(50, y, str(lote['especie']))
            p.drawString(250, y, f"{lote['peso_disponible_kg']} kg")
            p.drawString(400, y, f"${lote['precio_kg']}")
            y -= 20
    except Exception as e:
        p.drawString(50, y, f"Error al recuperar datos: {str(e)}")
    
    p.showPage()
    p.save()
    return response

# --- VISTA DE ESTADO/DIAGNÓSTICO DE BASE DE DATOS ---
def estado_bd(request):
    try:
        db_instance = DatabaseSingleton()
        conn = db_instance.get_connection()
        conn.rollback()
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
        
        estado = "Conectado Exitosamente (Singleton Activo)"
    except Exception as e:
        version = str(e)
        estado = "Error de Conexión"
    
    return render(request, 'logistica_app/estado_bd.html', {
        'estado': estado,
        'version': version
    })

# --- VISTA DE LOGOUT ---
def logout_view(request):
    request.session.flush()
    return redirect('login')

CATEGORIAS = ["Pescado Blanco", "Crustáceos", "Moluscos"]

# --- VISTA DE REGISTRO DE CAPTURA (MÓDULO DE CAPTURA) ---
def registrar_captura(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('rol_id') != 1:   # solo acopio
        return redirect('dashboard_restaurante')

    if request.method == 'POST':
        especie = request.POST.get('especie', '').strip()
        categoria = request.POST.get('categoria', '').strip()
        peso = request.POST.get('peso_disponible_kg', '').strip()
        precio = request.POST.get('precio_kg', '').strip()

        errores = []
        if not especie:
            errores.append('La especie es obligatoria.')
        if categoria not in CATEGORIAS:
            errores.append('Selecciona una categoría válida.')
        try:
            peso_kg = float(peso.replace(',', '.'))
            if peso_kg <= 0: errores.append('El peso debe ser mayor a 0.')
        except ValueError:
            peso_kg = None; errores.append('El peso debe ser un número válido.')
        try:
            precio_kg = float(precio.replace(',', '.'))
            if precio_kg <= 0: errores.append('El precio debe ser mayor a 0.')
        except ValueError:
            precio_kg = None; errores.append('El precio debe ser un número válido.')

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'logistica_app/registro_captura.html', {
                'categorias': CATEGORIAS,
                'form': {'especie': especie, 'categoria': categoria, 'peso': peso, 'precio': precio},
            })

        try:
            lote_id = lote_repository.crear_lote(
                request.session.get('usuario_id'), especie, categoria, peso_kg, precio_kg)
            messages.success(request, f'Lote de {especie} publicado correctamente (ID {lote_id}).')
            return redirect('dashboard_acopio')
        except Exception as e:
            messages.error(request, f'Error al registrar la captura: {str(e)}')

    return render(request, 'logistica_app/registro_captura.html', {
        'categorias': CATEGORIAS, 'form': {},
    })


# --- ACTUALIZA TU VISTA EXISTENTE ---
def dashboard_restaurante(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    categoria = request.GET.get('categoria', '')
    if categoria not in CATEGORIAS:
        categoria = ''
    try:
        lotes = lote_repository.obtener_disponibles(categoria or None)
    except Exception as e:
        print(f"Error cargando lotes: {e}")
        lotes = []
    return render(request, 'logistica_app/dashboard_restaurante.html', {
        'nombre': request.session.get('nombre'),
        'lotes': lotes,
        'categorias': CATEGORIAS,
        'categoria_activa': categoria,
    })

def agregar_pedido(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        id_lote = request.POST.get('id_lote')
        kg_str = request.POST.get('kg_solicitados')
        
        try:
            kg = float(kg_str.replace(',', '.'))
            if kg <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Ingresa una cantidad de kg válida.")
            return redirect('dashboard_restaurante')

        try:
            pedido_repository.crear_pedido(id_lote, request.session['usuario_id'], kg)
            messages.success(request, f"Pedido de {kg} kg agregado exitosamente.")
        except Exception as e:
            messages.error(request, f"No se pudo procesar el pedido: {str(e)}")
            
    return redirect('dashboard_restaurante')

def mis_pedidos(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    
    pedidos = pedido_repository.obtener_por_usuario(request.session['usuario_id'])
    
    return render(request, 'logistica_app/mis_pedidos.html', {
        'nombre': request.session.get('nombre'),
        'pedidos': pedidos
    })