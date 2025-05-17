import socket

def list_to_dict(list):
  return {"이름": list[0], "학과": list[1], "학번": list[2]}  

if __name__ == "__main__":
    host = '127.0.0.1' #루프백 주소(localhost)
    port = 1111 #사용할 포트

    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #소켓 생성(IPv4, TCP)
    socket.bind((host, port)) #IP주소와 소켓 묶기(튜플 형태로 전달)
    socket.listen(1) #1개의 클라이언트 소켓 요청 대기

    conn, addr = socket.accept() #클라이언트 접속 요청 수락(새 소켓 객체, 클라이언트의 주소)
    client = conn.recv(1024).decode('utf-8') #최대 1024바이트 수신, 문자열로 디코딩
    client_list = client.strip("[]").replace("'", "").split(', ') #리스트 형태로 변환
    print("Recv ",list_to_dict(client_list)) #딕셔너리 형태로 출력
    conn.close() #소켓 닫기
    socket.close() #서버 소켓 닫기
