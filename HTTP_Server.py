# COMP 445 - ASSIGNMENT 2
# Tri-Luong Steven Dien
# 27415281

import socket
import os
import time
from packet import Packet


def run_server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        listener.bind(("", port))
        print('Server is listening at port', port)
        while True:
            data, sender = listener.recvfrom(1024)
            handle_client(listener, data, sender)
    finally:
        listener.close()


def handle_client(conn, data, router_address):
    p = Packet.from_bytes(data)

    sequence_number = p.seq_num
    decoded_data = p.payload.decode("utf-8")

    print('Router: ', router_address)
    print('Packet: ', p)
    print("router_address: ", p.peer_ip_addr)
    print('Payload: ', decoded_data)

    try:
        useful_data = decoded_data.split(" HTTP/")[0]
        print(decoded_data)

        if 'GET' in useful_data:
            get_request(conn, useful_data, p.peer_ip_addr, p.peer_port, router_address, sequence_number)

        if 'POST' in useful_data:
            post_request(conn, useful_data, p.peer_ip_addr, p.peer_port, router_address, sequence_number)

        if p.packet_type == 1 and p.seq_num == 0:
            p = Packet(packet_type=2,
                       seq_num=sequence_number,
                       peer_ip_addr=p.peer_ip_addr,
                       peer_port=p.peer_port,
                       payload="")
            conn.sendto(p.to_bytes(), router_address)

    except FileNotFoundError:
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=p.peer_ip_addr,
                   peer_port=p.peer_port,
                   payload="404 NOT FOUND")
        conn.sendto(p.to_bytes(), router_address)

    except PermissionError:
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=p.peer_ip_addr,
                   peer_port=p.peer_port,
                   payload="403 Forbidden")
        conn.sendto(p.to_bytes(), router_address)

    except OSError:
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=p.peer_ip_addr,
                   peer_port=p.peer_port,
                   payload="400 BAD REQUEST")
        conn.sendto(p.to_bytes(), router_address)

    finally:
        print('Client from', router_address, 'has disconnected')


def get_request(conn, useful_data, peer_address, peer_port, router_address, sequence_number):
    useful_data = useful_data.replace("%20", " ")
    content = ""

    if "d=" in useful_data:
        directory = "." + useful_data.split("d=")[1]
    else:
        directory = '.'

    folder = os.listdir(directory)

    if len(useful_data) > 5:
        file_requested = useful_data.split("/")[1]
        file_requested = file_requested.split("?")[0]

        if "-d" in file_requested:
            file_requested = file_requested.split("d=")[0]

        for f in folder:
            file_name = f.split('.')[0]
            if f.startswith(file_requested) and file_requested == file_name:
                f = open(directory + "/" + f, 'r')
                content = f.read()
                break
            else:
                content = "404"

        if "404" in content:
            response = http_response(404, 0) + "<html><body><p>"
            content = ""
        else:
            response = http_response(200, len(content)) + "<html><body><p>"

    elif len(useful_data) == 5:
        all_files = ""
        for f in folder:
            if f == "HTTP_Server.py":
                continue
            else:
                all_files += "/" + f + "<br />"
        content += all_files

    response = http_response(200, len(content)) + "<html><body><p>"
    response += content
    response = response.encode("utf-8")

    p = Packet(packet_type=0,
               seq_num=sequence_number,
               peer_ip_addr=peer_address,
               peer_port=peer_port,
               payload=response)

    conn.sendto(p.to_bytes(), router_address)


def post_request(conn, useful_data, peer_address, peer_port, router_address, sequence_number):
    content = ""

    try:
        if "d=" in useful_data:
            directory = "." + useful_data.split("d=")[1]
            file_requested = useful_data.split("/")[1]
            file_requested = file_requested.split("?")[0]

            if "c=" in useful_data:
                directory = directory.split("&")[0]
                content = useful_data.split("c=")[1]
                content = content.replace("%20", " ")
                content = content.replace("+", " ")
        else:
            directory = '.'
            file_requested = useful_data.split("/")[1]

            if "c=" in useful_data:
                file_requested = file_requested.split("?")[0]
                content = useful_data.split("c=")[1]
                content = content.replace("%20", " ")
                content = content.replace("+", " ")

        if os.path.isfile(directory + "/" + file_requested):
            output_file = open(directory + "/" + file_requested, 'w')
            output_file.write(content)
            return_message = "File Overwritten<br />" + content
        else:
            output_file = open(directory + "/" + file_requested, 'w')
            output_file.write(content)
            return_message = "New File Created<br />" + content

        response = http_response(200, len(return_message)) + "<html><body><p>"
        response += return_message + "</p></body></html>"
        response = response.encode("utf-8")

        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=peer_address,
                   peer_port=peer_port,
                   payload=response)
        conn.sendto(p.to_bytes(), router_address)
    except FileNotFoundError:
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=peer_address,
                   peer_port=peer_port,
                   payload="404 NOT FOUND")
        conn.sendto(p.to_bytes(), router_address)
    except PermissionError:
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=p.peer_ip_addr,
                   peer_port=p.peer_port,
                   payload="403 Forbidden")
        conn.sendto(p.to_bytes(), router_address)
    except OSError:
        response = http_response(400, 0)
        p = Packet(packet_type=0,
                   seq_num=sequence_number,
                   peer_ip_addr=peer_address,
                   peer_port=peer_port,
                   payload=response)
        conn.sendto(p.to_bytes(), router_address)


def http_response(number, length):
    now = time.strftime("%c")

    if number == 200:
        response = "HTTP/1.1 200 OK\r\n"

    elif number == 404:
        response = "HTTP/1.1 404 Not Found\r\n"

    elif number == 400:
        response = "HTTP/1.1 400 Bad Request\r\n"

    elif number == 403:
        response = "HTTP/1.1 403 Forbidden\r\n"

    response += "Date: " + now + "\r\n" \
                + "Content-Length: " + str(length) + " ."\
                + "Content-Type: text/html\r\n" \
                + "\r\n"

    modified_http_response = response.replace("\r\n", "<br />")
    modified_http_response = modified_http_response.replace(" .", "<br />")
    response += modified_http_response

    return response


run_server('', 80)
