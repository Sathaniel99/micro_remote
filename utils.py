import socket

def obtener_ip_local():
    # Obtiene el nombre del host
    nombre_host = socket.gethostname()

    # Obtiene todas las direcciones IP asociadas al host
    direcciones_ip = socket.gethostbyname_ex(nombre_host)

    # Filtra direcciones IP internas (192.168.x.x, 10.x.x.x, 172.16.x.x)
    if direcciones_ip is None:
        # Si no se encuentra una IP local, devuelve la primera disponible
        return direcciones_ip[0] if direcciones_ip else "127.0.0.1"
    
    return direcciones_ip[0]

IP_enlazadas = {
    '169.254.185.236' : '169.254.23.244',
    '169.254.23.244' : '169.254.185.236',
}
