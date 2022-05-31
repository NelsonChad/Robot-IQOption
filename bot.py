from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
import sched, time, json
import threading
import sys

API = IQ_Option("tonnylson.chad@gmail.com", "pass")

API.set_max_reconnect(3) # Valor negativo irá deixar o numero máximo de reconexões infinito(cuidado)!
ATIVOS = API.get_all_open_time()

API.change_balance('PRACTICE')

PAYOUT = 50
MARTINGALE = 2
MERCADO = 0
ENTRADA = 0
OPCAO = "Binarias"
def profile():
    prof = json.loads(json.dumps(API.get_profile()))
    return prof['result']


def getData(): 
    x = profile()
    print('>>>>>CONTA: ', x['name'])
    print('>>>>>NICK: ', x['nickname'])
    print('>>>>>SALDO: '+ str(API.get_balance())+'$')

    menu()

#MENU
def menu():
    global MERCADO
    ans=True
    while ans:
        print("""==========================MENU============================
        1.Mercado Normal
        2.Mercado OTC
        4.Exit/Quit
        """)
        ans = input("Selecione O mercado Desejado: ")
        if ans=="1":
          print("\n ==>Escolheu Mercado Normal")
          MERCADO = 1
          typeOptions()
        elif ans=="2":
          print("\n ==>Escolheu Mercado OTC")
          MERCADO = 2
          typeOptions()
        elif ans=="4":
          print("\n Goodbye") 
          exit()
          ans = None
        else:
           print("\n Opcao Invelida")

def typeOptions():
    global OPCAO
    ans1=True
    while ans1:
        print("""==========================OPC=============================
        1.Opcoes Binarias
        2.Opcoes Digitais
        """)
        ans1 = input("Selecione tipo de Opcao desejado: ")
        if ans1=="1":
          print("\n ==>Binarias<==")
          OPCAO = "Binarias"
          config()
        elif ans1=="2":
          print("\n ==>Digital<==")
          OPCAO = "Digital"
          config()
        else:
           print("\n Opcao Invelida")

def config():
    global ENTRADA
    global PAYOUT
    PAYOUT = input("Digite o PAYOUT minimo: ")
    ENTRADA = input("Digite a entrada das suas operacoes: ")

    if MERCADO == 1:
         print("MERCADO NORMAL")
    if MERCADO == 2:
         print("MERCADO OTC")
         
   
    print("PAYOUT: ", PAYOUT,"%")
    print("Entrada: ", ENTRADA)
    print("==========================================================")

    op = input("""Confirma os Dados?
                    S- Sim
                    N-Nao
                """)
    if op.lower() == "s":
       start()
    else:
        menu()


def checkActives():
    ATIVOS = API.get_all_open_time()

    for tipo, data in ATIVOS.items():
        for ativo_nome,value in data.items():
            print(tipo,ativo_nome,value["open"])


def buyDigitalListFile(Entrada,Paridade,Direcao,Duracao,Hora):
    sys.stdout.write('\a')
    sys.stdout.write('\n')

    now = datetime.now()
    time_sec_now = time.mktime(now.timetuple())

    global PAYOUT
    global MARTINGALE

    print('=================================OPERANDO==================================')
    print('Activo= '+Paridade+' Entrada='+str(Entrada)+'$ Opcao= '+Direcao+' Duracao= '+str(Duracao)+'M')

    ganhou = False

    #checa se ainda esta dentro da Hora
    if time_sec_now > Hora:
        print('+++++++++++++++SINAL EXPIRADO++++++++++++++')
    else:

        API.subscribe_strike_list(Paridade, int(Duracao))
        statusPayout = True

        while statusPayout and ganhou == False:
            data = API.get_digital_current_profit(Paridade, int(Duracao))
            
            if data == False:
                print('SEM Payout: '+str(data)) # Nos primeiros retornos pode vir "False", aguarde alguns segundos que começara a retornar os valores do tipo float
            else:
                statusPayout = False
                print('Payout: '+str(data)) # Nos primeiros retornos pode vir "False", aguarde alguns segundos que começara a retornar os valores do tipo float

                if(int(data) >= int(PAYOUT)): #Caso o payout esteja bom
                    print('OPERAVEL '+str(PAYOUT))
                    id = API.buy_digital_spot(Paridade, float(Entrada), str(Direcao).lower(), int(Duracao))
                    if id != "error":
                        while True:
                            status,lucro = API.check_win_digital_v2(id) #pega o status da operacao
                            if status == True:
                                break
                        if lucro < 0:
                            print("Voce perdeu "+str(lucro)+"$")
                            
                            gale = 1
                            #MARTINGALE
                            while ganhou == False and MARTINGALE > 0:
                                
                                id2 = False
                                if MARTINGALE == 2:
                                    id2 = API.buy_digital_spot(str(Paridade), float(Entrada)*2, str(Direcao).lower(), int(Duracao))
                                elif MARTINGALE == 1:
                                    id2 = API.buy_digital_spot(str(Paridade), float(Entrada)*4, str(Direcao).lower(), int(Duracao))

                                print(gale,"º MARTINGALE-OTC MG: ", MARTINGALE)
                                if id2 != "error":

                                    while True:
                                        status,lucroM = API.check_win_digital_v2(id2) 
                                        #pega o status da operacao
                                        if status == True:
                                            break
                                    if lucroM < 0:
                                        print("Perdeu o ",gale,"º MARTINGALE"+str(lucroM)+"$ OTC")
                                        MARTINGALE = MARTINGALE - 1
                                        gale = gale + 1
                                        if gale == 2:
                                            print('___________________________________________________________________________')
                                        
                                    else:
                                        print("Voce ganhou "+str(lucroM)+"$ NO",gale," MARTINGALE")
                                        print('===========================================================================')
                                        ganhou = True
                        else:
                            print("Voce ganhou "+str(lucro)+"$")
                            print('===========================================================================')
                            ganhou = True
                    else:
                        print("Por favor, tente novamente: "+id)
                        print('===========================================================================')

                        # Fim IF
                else:
                    print('NAO OPERAVEL '+str(PAYOUT))
                    
            time.sleep(1)   

def buyBinaryListFile(Entrada,Paridade,Direcao,Duracao,Hora):
    sys.stdout.write('\a')
    global PAYOUT
    PAYOUT_B = float(PAYOUT)/100
    global MARTINGALE

    print('Entrada='+str(Entrada)+' Paridade= '+Paridade+' Dir= '+Direcao+' Duracao= '+str(Duracao))

    ganhou = False

    API.subscribe_strike_list(Paridade, int(Duracao))
    statusPayout = True

    while statusPayout and ganhou == False:
        d = API.get_all_profit()
        pay = d[Paridade]["binary"]
        
        print('Payout 1min: '+str(float(d[Paridade]["binary"])*100)) 
        print('Payout 5+: '+str(float(d[Paridade]["turbo"])*100))

        if(int(pay) >= int(PAYOUT_B)): #Caso o payout esteja bom
            print('OPERAVEL '+str(PAYOUT))
            id = API.buy(int(Entrada), Paridade, str(Direcao).lower(), int(Duracao))
            if id != "error":
                while True:
                    status,lucro = API.check_win_v4(id) #pega o status da operacao
                    if status == True:
                        break
                if lucro < 0:
                    print("Voce perdeu "+str(lucro)+"$")
                    
                    gale = 1
                    #MARTINGALE
                    while ganhou == False and MARTINGALE > 0:
                        
                        id2 = False
                        if MARTINGALE == 2:
                            id2 = API.buy(float(Entrada)*2, str(Paridade), str(Direcao).lower(), int(Duracao))
                        elif MARTINGALE == 1:
                            id2 = API.buy(float(Entrada)*4, str(Paridade), str(Direcao).lower(), int(Duracao))

                        print(gale,"º MARTINGALE MG: ", MARTINGALE, " OB")
                        if id2 != "error":

                            while True:
                                status,lucroM = API.check_win_v4(id2) 
                                #pega o status da operacao
                                if status == True:
                                    break
                            if lucroM < 0:
                                print("Perdeu o ",gale,"º MARTINGALE"+str(lucroM)+"$ OB")
                                MARTINGALE = MARTINGALE - 1
                                gale = gale + 1
                                if gale == 2:
                                    print('___________________________________________________________________________')
                                
                            else:
                                print("Voce ganhou "+str(lucroM)+"$ NO",gale," MARTINGALE")
                                print('===========================================================================')
                                ganhou = True
                        else:
                            print("Voce ganhou "+str(lucro)+"$ OB")
                            print('===========================================================================')
                            ganhou = True
                    else:
                        print("Por favor, tente novamente: "+id)
                        print('===========================================================================')

            else:
                print("Por favor, tente novamente: ",id)
                # Fim IF
        else:
            print('NAO OPERAVEL '+str(PAYOUT))
            
    time.sleep(1)   

def buyBinaryListFile():
    Entrada = 100
    Paridade = "EURUSD"
    Direcao = "call" # Ou "put"
    Duracao = 1

    sys.stdout.write('\a')
    global PAYOUT
    PAYOUT_B = int(PAYOUT)
    global MARTINGALE

    print('Entrada='+str(Entrada)+' Paridade= '+Paridade+' Dir= '+Direcao+' Duracao= '+str(Duracao))

    ganhou = False

    API.subscribe_strike_list(Paridade, int(Duracao))
    statusPayout = True;

    while statusPayout and ganhou == False:
        #data = API.get_digital_current_profit(Paridade, int(Duracao))
        d = API.get_all_profit()

        #print(d["CADCHF"]["turbo"])
        pay = d[Paridade]["binary"]
        
        
        print('Payout 1min: '+str(float(d[Paridade]["binary"])*100)) 
        print('Payout 5+: '+str(float(d[Paridade]["turbo"])*100))

        if(float(pay)*100 >= float(PAYOUT_B)): #Caso o payout esteja bom

            print('OPERAVEL')

            status1,id = API.buy(int(Entrada), Paridade, str(Direcao).lower(), int(Duracao))
            print("Lucr: ",id," status: ",status1)
            if status1 == True:
                print("No IF")

                
                status,lucro = API.check_win_v4(id) #pega o status da operacao                    
                print('Lucro: ', lucro)

                if lucro < 0:
                    print("Voce perdeu "+str(lucro)+"$")
                    
                    gale = 1
                    #MARTINGALE
                    while ganhou == False and MARTINGALE > 0:
                        
                        id2 = False
                        if MARTINGALE == 2:
                            status2,id2 = API.buy(float(Entrada)*2, str(Paridade), str(Direcao).lower(), int(Duracao))
                        elif MARTINGALE == 1:
                            status2,id2 = API.buy(float(Entrada)*4, str(Paridade), str(Direcao).lower(), int(Duracao))

                        print(gale,"º MARTINGALE MG: ", MARTINGALE, " OB")
                        if status2 == True:
                            status,lucroM = API.check_win_v4(id2)

                            if lucroM < 0:
                                print("Perdeu o ",gale,"º MARTINGALE"+str(lucroM)+"$ OB")
                                MARTINGALE = MARTINGALE - 1
                                gale = gale + 1
                                if gale == 2:
                                    print('___________________________________________________________________________')
                                
                            else:
                                print("Voce ganhou "+str(lucroM)+"$ NO",gale," MARTINGALE")
                                print('===========================================================================')
                                ganhou = True
                else:
                    print("Voce ganhou "+str(lucro)+"$ OB")
                    print('===========================================================================')
                    ganhou = True
            else:
                print("Por favor, tente novamente: ",id)
                # Fim IF
        else:
            print('NAO OPERAVEL '+str(PAYOUT))
            
    time.sleep(1)   

def schedule_with_FileDigital():

    global ENTRADA
    global MERCADO
    hh = 0
    mm = 0
    ss = 52
    ninute = mm - 1
    Entrada = ENTRADA
    i = 0

    job = []
    now = datetime.now()
    print("::::::::::::::::::::::::::::::::HOJE:::::::::::::::::::::::::::::::::::")
    print(":::::::::::::::::::: ", now," :::::::::::::::::::::")
    print(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

    arquivo = open('lista.txt', 'r')
       
    for line in arquivo:
        print('|-----------------------------ACTIVO ',i+1,'------------------------------|')

        if MERCADO == 1:
            print('TEMPO: '+line[0:2]+' ACTIVO: '+line[3:9]+' HORA: ',int(line[10:12])+5,':'+line[13:15]+' OP: '+ line[19:23])
            t1 = (2020, 4, 6, int(line[10:12])+5, int(line[13:15])-1, ss, 1, 48, 0)
            Paridade = line[3:9]
            Duracao = line[1:2]

            if (line[19:22] == 'PUT'):
                Direcao = line[19:22]# ou put
            else:
                Direcao = line[19:23] # ou put

        if MERCADO == 2:
            print('TEMPO: '+line[0:2]+' ACTIVO: '+line[3:13]+' HORA: ',int(line[14:16])+5,':'+line[17:19]+' OP: '+ line[23:27])
            #t = (ano,mes,dia,hh,mm,ss, 1, 48, 0) tuple positions
            t1 = (2020, 4, 6, int(line[14:16])+5, int(line[17:19])-1, ss, 1, 48, 0)
            Paridade = line[3:13]
            Duracao = line[1:2]

            if (line[23:26] == 'PUT'):
                Direcao = line[23:26]# ou put
            else:
                Direcao = line[23:27] # ou put
        
        
          
        time_sec = time.mktime(t1) 


        # datetime object containing current date and time
        time_sec_now = time.mktime(now.timetuple())

        if time_sec_now >= time_sec:
           print('STATUS: Sinal Ultrapassado')
           print('|----------------------------------------------------------------------|')
        else: 
            x = threading.Thread(target=run, args=(Entrada,Paridade,Direcao,Duracao,time_sec)) 
            #x = sch.enterabs(time_sec, i, buyDigitalListFile, (Entrada,Paridade,Direcao,Duracao,time_sec))
            print('STATUS: Agendado')
            print('|---------------------------------------------------------------------|')

            job.append(x)

        i = i + 1

    print('************************ ',len(job),' Sinais Agendados**************************')
        
    for j in job:
        j.start()
        print('******Agendado********')

    sys.stdout.write('\n\n\n')



def run(Entrada,Paridade,Direcao,Duracao,Hora):
    global OPCAO
    sch = sched.scheduler(time.time, time.sleep)
    if OPCAO == "Binarias":
        sch.enterabs(Hora, 1, buyBinaryListFile, (Entrada,Paridade,Direcao,Duracao,Hora))
    if OPCAO == "Digital":
        sch.enterabs(Hora, 1, buyDigitalListFile, (Entrada,Paridade,Direcao,Duracao,Hora))
    sch.run()

def openList():
    arquivo = open('lista.txt', 'r')
   
    for line in arquivo:
        #print(line)
        print('TEMPO: '+line[0:2]+' ACTIVO: '+line[3:13]+' HORA: ',int(line[14:16])+5,':'+line[17:19]+' OP: '+ line[23:27])

        #Entrada = 10
        #Paridade = line[3:9]
        #Direcao = line[19:23] # Ou "put"
        #Duracao = int(line[1:2])
    arquivo.close()

def start():
    buyBinaryListFile()
    #schedule_with_FileDigital()

def main():
    while True:
        if API.check_connect() == False: # Detecta se o WebSocket está conectado ou não
            print(">>>>>Conexao perdida, tentando reconectar..")
            API.connect() #Realizando a conexão novamente
            print(">>>>>Reconectado com sucesso!")
        else:
            sys.stdout.write('\n')
            print(">>>>>conectado com sucesso!")
            getData()
            #buyDigital()
        
            break
        time.sleep(1)

if __name__ == '__main__':
    main()



