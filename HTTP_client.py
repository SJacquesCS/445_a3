import socket
import os
import pygubu
import tkinter

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))


class MyApplication(pygubu.TkApplication):
    def _create_ui(self):
        self.builder = builder = pygubu.Builder()
        self.bad_request = False

        builder.add_from_file(os.path.join(CURRENT_DIR, '445_a1.ui'))

        self.mainwindow = builder.get_object('mainwindow')
        self.request = builder.get_object('req_entry')
        self.response = builder.get_object('resp_text')
        self.respscroll = builder.get_object("resp_scroll")
        self.respscroll.configure(command=self.response.yview)
        self.response['yscrollcommand'] = self.respscroll.set
        self.popular = builder.get_object("pop_text")
        self.popscroll = builder.get_object("pop_scroll")
        self.popscroll.configure(command=self.popular.xview)
        self.popular['xscrollcommand'] = self.popscroll.set
        self.message = builder.get_object('msg_entry')
        self.message.configure(foreground="snow4")

        builder.connect_callbacks(self)

    def quit(self):
        self.mainwindow.quit()

    def clear(self):
        self.response.delete("1.0", tkinter.END)
        self.message.configure(text="Enter a request, host, and port. Send the request to receive a reponse",
                               foreground="snow4")

    def run(self):
        self.mainwindow.mainloop()

    def parse_request(self):
        self.bad_request = False
        verbose = False
        output = False
        port = 80
        url_index = 0
        output_file = ""
        official_request = ""
        host = ""

        request = self.request.get().rstrip("\r\n")
        split = request.split(" ")

        if "httpc" in request:
            if "help" in request or "HELP" in request:
                self.help_request(request)
                return
            else:
                url = ""

                for i in range(0, len(split)):
                    if "http://" in split[i]:
                        url = split[i]
                        url_index = i
                    if "-o" in split[i]:
                        output = True
                        output_file = open(str(split[i + 1]), 'a')

                host = str(url.split("/")[2])

                print(request)

                if "get" in request or "GET" in request:
                    official_request = self.get_request(request, host)
                elif "post" in request or "POST" in request:
                    official_request = self.post_request(request, host)
                else:
                    self.bad_request = True
        else:
            self.bad_request = True

        if "-v" in request:
            verbose = True

        if self.bad_request:
            self.message.configure(text="Bad request, please try again.", foreground="red")
        else:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            print(official_request)

            try:
                conn.connect((host, port))
                encoded_request = official_request.encode("utf-8")
                conn.send(encoded_request)
                response = conn.recv(4096).decode("utf-8")
                conn.close()

                if "400 BAD REQUEST" in response:
                    self.message.configure(text="Bad request, please try again.", foreground="red")
                    return

                if "403 Forbidden" in response:
                    self.message.configure(text="This request is forbidden, please try a different one.",
                                           foreground="red")
                    return

                if "404 NOT FOUND" in response:
                    self.message.configure(text="Nothing to be found with this request, please try again.",
                                           foreground="red")
                    return

                if "503 SERVICE UNAVAILABLE" in response:
                    self.message.configure(text="Service currently unavailable, try again later.",
                                           foreground="red")
                    return

                while "302 FOUND" in response:
                    resp_split = response.split(" ")

                    redirect = ""

                    for i in range(0, len(resp_split)):
                        if "Location:" in resp_split[i]:
                            redirect = resp_split[i + 1].split("\r\n")[0]

                    new_url = "http://" + host + redirect

                    self.response.insert(tkinter.END, "Redirected to " + new_url
                                         + "\n\n---------------------------------------------\n\n")

                    if "get" in request or "GET" in request:
                        new_official_request = self.get_request(new_url, host)
                    elif "post" in request or "POST" in request:
                        new_official_request = self.post_request(new_url, host)

                    print(new_official_request)

                    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    conn.connect((host, port))
                    new_encoded_request = new_official_request.encode("utf-8")
                    conn.send(new_encoded_request)
                    response = conn.recv(4096).decode("utf-8")
                    conn.close()

                response += "\n---------------------------------------------\n\n"

                response = response.replace("<br />", "\n")
                response = response.replace("<br/>", "\n")
                response = response.replace("<br>", "\n")

                if verbose:
                    self.response.insert(tkinter.END, str(response))
                    if output:
                        output_file.write("\n" + response)
                        output_file.close()
                else:
                    self.response.insert(tkinter.END, str(response.split("\r\n\r\n")[1]))
                    if output:
                        output_file.write("\n" + response.split("\r\n\r\n")[1])
                        output_file.close()

                self.message.configure(text="Request accepted.", foreground="green")
            except IndexError:
                self.message.configure(text="Bad request, please try again.", foreground="red")

            conn.close()

    def get_request(self, request, host):
        try:
            official_request = ""
            headers = []
            contents = request.split(" ")

            official_request += "GET "

            if "-h" in contents:
                for x in range(contents.index("-h") + 1, len(contents) - 1):
                    if contents[x] != "-h" and contents[x] != "-v":
                        split = contents[x].split(":")
                        headers.append(str(split[0]) + ": " + str(split[1]))

            official_request += request.split(host)[1]

            official_request += " HTTP/1.0\r\nHost: " + str(host)

            print(official_request)

            if len(headers) > 0:
                official_request += "\r\n"

                for header in headers:
                    official_request += str(header) + "\r\n"

            return official_request + "\r\n\r\n"
        except IndexError:
            self.bad_request = True

    def post_request(self, request, host):
        try:
            official_request = ""
            contentlength = 0
            headers = []
            data = []
            contents = request.split(" ")

            official_request += "POST "

            if "-h" in contents:
                for x in range(contents.index("-h") + 1, len(contents) - 1):
                    if contents[x] == "-d"\
                            or contents[x] == "-f"\
                            or contents[x] == "-h"\
                            or contents[x] == "-v"\
                            or contents[x] == "-i"\
                            or contents[x] == "-o":
                        break

                    split = contents[x].split(":")
                    headers.append(str(split[0]) + ": " + str(split[1]))

            if "-i" in contents:
                try:
                    file = str(contents[contents.index("-i") + 1])
                    input_file = open(file)

                    for line in input_file:
                        data.append(line)
                        contentlength += len(line)
                except (OSError, IOError):
                    self.bad_request = True

            if "-d" in contents:
                for x in range(contents.index("-d") + 1, len(contents) - 1):
                    if contents[x] == "-d"\
                            or contents[x] == "-f"\
                            or contents[x] == "-h"\
                            or contents[x] == "-v"\
                            or contents[x] == "-i"\
                            or contents[x] == "-o":
                        break
                    contentlength += len(contents[x])

                    temp = contents[x].replace("'", "").rstrip("\r\n")
                    data.append(str(temp))

            official_request += contents[len(contents) - 1]

            official_request += " HTTP/1.0\r\nHost: " + str(host)

            if "Content-Length" not in contents:
                headers.append("Content-Length:" + str(contentlength))

            if len(headers) > 0:
                official_request += "\r\n"
                for header in headers:
                    official_request += str(header) + "\r\n"

            if len(data) > 0:
                official_request += "\r\n"
                for datum in data:
                    official_request += str(datum)

            official_request += "\r\n\r\n"

            return official_request
        except IndexError:
            self.bad_request = True

    def help_request(self, request):
        response = ""

        contents = request.split(" ")

        if len(contents) == 2:
            response = "httpc is a curl-like application but supports HTTP protocol only.\n\n" \
                       + "Usage: httpc command [arguments]\n\n" \
                       + "The commands are:\n" \
                       + "\tget\texecutes a HTTP GET request and prints the response.\n" \
                       + "\tpost\texecutes a HTTP POST request and prints the response.\n" \
                       + "\thelp\tprints this screen.\n\n" \
                       + "Use 'httpc help [command]' for more information about a command.\n\n"
        elif contents[2].lower() == "get":
            response = "Usage: httpc get [-v] [-h key:value] URL\n\n" \
                       + "Get executes a HTTP GET request for a given URL.\n\n" \
                       + "\t-v\t\tPrints the detail of the response such as protocol, status, and headers.\n" \
                       + "\t-h key:value\t\tAssociates headers to HTTP request with the format 'key:value'.\n\n"
        elif contents[2].lower() == "post":
            response = "Usage: httpc  httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL\n\n" \
                       + "Post executes a HTTP POST request for a given URL with inline data or from file.\n\n" \
                       + "\t-v\t\tPrints the detail of the response such as protocol, status, and headers.\n" \
                       + "\t-h key:value\t\tAssociates headers to HTTP request with the format 'key:value'.\n" \
                       + "\t-d string\t\tAssociates an inline data to the body HTTP POST request.\n" \
                       + "\t-f file\t\tAssociates the content of a file to the body HTTP POST request.\n\n" \
                       + "Either [-d] or [-f] can be used but not both.\n\n"

        response += "--------------------------------------------------------------------------\n\n"

        self.response.insert(tkinter.END, response)


if __name__ == '__main__':
    root = tkinter.Tk()
    root.resizable(width=False, height=False)
    root.title("Jacques' Request System")
    app = MyApplication(root)
    app.run()
