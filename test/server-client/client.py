import socket

def create_list():
  data = ["김희주", "경영정보학과", "20200294"]
  return data

if __name__ == "__main__":
    host = '127.0.0.1' #루프백 주소(localhost)
    port = 1111 #사용할 포트

    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #소켓 생성(로컬 통신, TCP)
    socket.connect((host, port)) #서버 소켓과 연결(튜플 형태로 전달)

    data = str(create_list()) #문자열로 변환(데이터가 네트워크를 통해 전송될 때 바이트 단위로 처리됨)
    socket.send(data.encode('utf-8')) #데이터 인코딩하여 전송
    print("Send ", create_list()) #전송된 데이터 출력
    socket.close() #소켓 닫기
