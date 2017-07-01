from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.core.text.markup import MarkupLabel
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from kivy.clock import Clock
from kivy.uix.vkeyboard import VKeyboard
from kivy.config import Config
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
import os.path
import sys
import pickle
from subprocess import call
import MySQLdb
import time
import datetime

# from datetime import datetime, time, timedelta



try:
    global db
    db = MySQLdb.connect(host="nuvolino.mysql.database.azure.com",    # your host, usually localhost
                     user="nuvolino@nuvolino",         # your username
                     passwd="RossiniEnergy123",  # your password
                     db="sql11172989",
                     connect_timeout = 10) 

except Exception:
    db = None
    print "Impossible to Connect to DB"
    # print "Error %d: %s" % (e.args[0],e.args[1])
Config.set('kivy', 'keyboard_mode', 'dock')

# Recuperation energie precedente en utlisant pickle
global table

energie   = 0
Pinst     = 0
seconds   = 0
table = "";

File = open("/home/pi/Documents/Nuvola/table.txt","r")
#File = open("table.txt","r")
lines = File.readlines()
table = lines[0]
File.close()



# try:
#     cur = db.cursor()
#     string = 'SELECT Seconds, Energy, Pinst  FROM sql11172989.Nuvolino ORDER BY DATE_ DESC LIMIT 1;'
#     cur.execute(string)
#     for row in cur.fetchall():
#         seconds = row[0]
#         energie = row[1]
#         Pinst = row[2]
        
# except Exception:
    # print "Impossible to Connect to DB"
    # print "Using Backup info"      

if os.path.isfile('backup3.p'):
    try:
        output   = open('backup3.p', 'rb')
        data     = pickle.load(output)
        energie  = data[0]
        Pinst    = data[1]
        seconds  = data[2]
    except Exception:
        print "Accessing backup info"
        output  = open('backup5.p', 'rb')
        data    = pickle.load(output)
        energie = data[0]
        Pinst   = data[1]
        seconds = data[2]
else:	
    print "all zero"
    energie   = 0
    Pinst     = 0
    seconds   = 0


# Grille pour l'affichage compteur
class compteurlayout(GridLayout):
    def __init__(self, **kwargs):
        
        super(compteurlayout, self).__init__(**kwargs)
        global conn_status, state_of_charge, grid_power, state, battery_alarm, battery_current, battery_voltage, connect_to_db, block_recharge, finish_time

        state_of_charge = 0
        state = 0
        battery_alarm = 0
        battery_current = 0
        battery_voltage = 0
        connect_to_db = False
        grid_power = [0,0,0]
        conn_status = False
        conn_to_ccgx = False
        block_recharge = False
        self.cols = 2
        self.add_widget(Label(text='Potenza istantanea',font_size='25sp')) #,on_ref_press=self.cyclic))
        self.puissance = Label(text=' ',font_size='25sp')
        self.add_widget(self.puissance)
        # self.add_widget(Label(text='Energia autoconsumata', font_size='25sp'))
        # self.energy = Label(text=' ',font_size='25sp')
        # self.add_widget(self.energy)
        self.add_widget(Label(text='Carica batteria', font_size='25sp'))
        self.battery = Label(text=' ',font_size='25sp')
        self.add_widget(self.battery)
        
        self.add_widget(Label(text='Euro risparmiati', font_size='25sp'))
        self.euros = Label(text=' ',font_size='25sp')
        self.add_widget(self.euros)
        self.add_widget(Label(text='Euro risparmiati dopo un anno', font_size='25sp'))
        self.euros_year = Label(text=' ',font_size='25sp')
        self.add_widget(self.euros_year)
        self.ccgx = Label(text='[color=ff3333]Hello[/color][color=3333ff]World[/color]',font_size='15sp', markup = True)
        self.add_widget(self.ccgx)    
        self.db = Label(text='DB: NO',font_size='15sp', markup = True)
        self.add_widget(self.db)
        # self.add_widget(


        self.add_widget(Button(text='Reset',on_press=self.mdp_screen,size_hint_y=None, height=70, font_size='25sp'))
        self.add_widget(Button(text='Chiudi',on_press=self.mdp_screen_close,size_hint_y=None, height=70, font_size='25sp'))
        # self.statblock = Label(text='Disattivato',font_size='15sp', height=70)
        self.statblock = Button(text='Abilita/Disabilita blocco scarica',on_press=self.mdp_enable,size_hint_y=None, height=70, font_size='15sp')
        self.add_widget(self.statblock)
        
	Clock.schedule_interval(self.cyclic_compteur, 1.5)

    def cyclic_compteur(self,dt):
        global finish_time, block_recharge
         # cyclique d'affichage
        self.puissance.text = str(Pinst)+" W"
#	if Pinst > 0:
#		energie += Pinst
#	print(energie/3600000.0)
        self.battery.text=str(state_of_charge)
    # self.energy.text = str(round(energie/1,3))+" kWh"
	self.euros.text = str(round(energie/1*0.18,3))+" eur"
    
	if (connect_to_db ==False):
	    self.db.text = 'Conn. DB: [color=FF0000]No[/color]'
	else:
	    self.db.text = 'Conn. DB: [color=55FF00]Yes[/color]'  
        
    
    
	if (conn_status == False):
        # self.energy.text = "N/A"
	    self.puissance.text = "N/A"
	    self.euros.text = "N/A"
	    self.ccgx.text = 'Conn. CCGX: [color=FF0000]No[/color]'
            self.battery.text= "N/A"
        
        # self.euros_year.text = "N/A"
	else:
	    self.ccgx.text = 'Conn. CCGX: [color=55FF00]Yes[/color]'
        
	    if (seconds>24*60*60):
		    self.euros_year.text = str(round(energie/seconds/1*0.2*31536000*1,3))+" eur"
	    else:
		    self.euros_year.text = "Dati non sufficienti"
        
        if (block_recharge==True):
            if (self.dateDiffInSeconds(datetime.datetime.now(),finish_time) <2):
                client = ModbusClient('192.169.1.107', port=502)
                if (client.connect()):
                    client.write_register(2702, 100, unit=100)
                    block_recharge=False
                    self.statblock.text = "blocco scarica: Disattivato"
            else:
                self.statblock.text = "Scarica disabilitata: " + str(self.daysHoursMinutesSecondsFromSeconds(self.dateDiffInSeconds(datetime.datetime.now(),finish_time) ))
            
        
        
    def mdp_screen(self,*args):
	global my_screenmanager
	my_screenmanager.switch_to(ecran_mdp)

    def mdp_screen_close(self,*args):
	global my_screenmanager
	my_screenmanager.switch_to(mdp_close_screen)
    
    def dateDiffInSeconds( self, date1, date2):
      timedelta = date2 - date1
      return timedelta.days * 24 * 3600 + timedelta.seconds

    def daysHoursMinutesSecondsFromSeconds(self, seconds):
    	minutes, seconds = divmod(seconds, 60)
    	hours, minutes = divmod(minutes, 60)
    	days, hours = divmod(hours, 24)
    	return (hours, minutes, seconds)
        
    def mdp_enable(self,*args):
        global block_recharge, finish_time
        client = ModbusClient('192.169.1.107', port=502)
        # self.statblock.text = "24:00:00"

        # print block_recharge
        try:
            if (block_recharge==True):
                if (client.connect()):
                    client.write_register(2702, 100, unit=100)
                    block_recharge=False
                    self.statblock.text = "blocco scarica: Disattivato"
                else:
                    self.statblock.text = "blocco scarica: Servizio non disponibile"

            else:
                if (client.connect()):
                    client.write_register(2702, 1, unit=100)
                    block_recharge=True
                    self.statblock.text = "24:00:00"
                    finish_time = datetime.datetime.now() + datetime.timedelta(hours=12)
                    self.statblock.text = "Scarica disabilitata: " + str(self.daysHoursMinutesSecondsFromSeconds(self.dateDiffInSeconds(datetime.datetime.now(),finish_time) ))
                else:
                    self.statblock.text = "blocco scarica: Servizio non disponibile"

        except Exception:
            print "error"
            block_recharge=False
            self.statblock.text = "blocco scarica: Servizio non disponibile"
        client.close()
    
    

        

		
	
class compteur(Screen):
    #energie = 0
    def __init__(self, **kwargs):
        super(compteur, self).__init__(**kwargs)
	layout = compteurlayout()
	self.add_widget(layout)


class mdplayoutClose(GridLayout):
    def __init__(self, **kwargs):
        super(mdplayoutClose, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='Password', font_size='25sp')) #,on_ref_press=self.cyclic))
        self.mdpbox = TextInput(text='', font_size='25sp')
	self.add_widget(self.mdpbox)
	self.add_widget(Button(text='Ok', on_press=self.verify, font_size='25sp'))
	self.add_widget(Button(text='Cancel', on_press=self.cancel, font_size='25sp'))

    def cancel(self,*args):
	global my_screenmanager
	my_screenmanager.switch_to(ecran_compteur) 

    def verify(self,*args):
	print(self.mdpbox.text)
	if self.mdpbox.text == '1234':
		sys.exit(0)
		
		
	
class mdplayout(GridLayout):
    def __init__(self, **kwargs):
        super(mdplayout, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='Password', font_size='25sp')) #,on_ref_press=self.cyclic))
        self.mdpbox = TextInput(text='', font_size='25sp')
	self.add_widget(self.mdpbox)
	self.add_widget(Button(text='Ok', on_press=self.verify, font_size='25sp'))
	self.add_widget(Button(text='Cancel', on_press=self.cancel, font_size='25sp'))
	#self.player = VKeyboard(layout='numeric.json')
	#self.add_widget(self.player)	

    def cancel(self,*args):
	global my_screenmanager
	my_screenmanager.switch_to(ecran_compteur) 

    def verify(self,*args):
	global my_screenmanager, energie, seconds
	print(self.mdpbox.text)
	if self.mdpbox.text == '1234':
		energie = 0
		seconds = 0
		call(["rm","log.txt"])
		with open("log.txt", "w") as myfile:
			myfile.write("seconds" + "\t" + "energy" + "\t" + "Inst power" + "\t" + "state charge" + "\t" + "conn status" + "\t" + "grid power 1" + "\t" + "grid power 2" + "\t" + "grid power 3" + "\t" + "state"  + "\t" + "battery alarm" + "\n")
			myfile.close()
		my_screenmanager.switch_to(ecran_compteur)
		self.mdpbox.text = ''; 

class mdp(Screen):
   def __init__(self, **kwargs):
	global energie, seconds
	super(mdp, self).__init__(**kwargs)
	layout = mdplayout()
	self.add_widget(layout)
	
class mdpClose(Screen):
   def __init__(self, **kwargs):
	super(mdpClose, self).__init__(**kwargs)
	layout = mdplayoutClose()
	self.add_widget(layout)
    
my_screenmanager = ScreenManager()
ecran_compteur = compteur(name='Compteur')
ecran_mdp = mdp(name='mdp')
mdp_close_screen = mdpClose(name='mdp_close')



class MyApp(App):
    def build(self):
        global time_check, conn_to_ccgx
        conn_to_ccgx = False
        
        time_check=1
	print energie
	my_screenmanager.add_widget(ecran_compteur)
	#my_screenmanager.add_widget(ecran_mdp)
    
    
	Clock.schedule_interval(self.cyclic, 1)

        return my_screenmanager

    def cyclic(self,dt):
        global energie,Pinst, conn_to_ccgx, seconds, conn_status, time_check, state_of_charge, grid_power, state, battery_alarm, battery_voltage, battery_current, connect_to_db
        client = ModbusClient('192.169.1.107', port=502)
        if (conn_status or (conn_status==False and time_check > 10)):
            try:
                conn_to_ccgx = False
                
                if (client.connect()):
                    
                    conn_to_ccgx = True
                    try:
                        
				               # print("connected")
                        rr = client.read_holding_registers(12, 3, unit=246)
            #rr = 1
                        if rr.getRegister(0)>32767:
                            Pinst = rr.getRegister(0)-65535
                        else:
                            Pinst = rr.getRegister(0)
                        if rr.getRegister(1)>32767:
                            Pinst += rr.getRegister(1)-65535
                        else:
                            Pinst += rr.getRegister(1)
                        if rr.getRegister(2)>32767:
                            Pinst += rr.getRegister(2)-65535
                        else:
                            Pinst += rr.getRegister(2)

                        soc = client.read_holding_registers(30, 2, unit=246) 
                        state_of_charge = soc.getRegister(0)/10
                        state = soc.getRegister(1)

                        battery_alarm_buffer = client.read_holding_registers(35, 1, unit=246) 
                        battery_alarm = battery_alarm_buffer.getRegister(0)


                        grid_ac = client.read_holding_registers(2600, 3, unit=30)

                        if grid_ac.getRegister(0)>32767:
                            grid_power[0] = grid_ac.getRegister(0)-65535
                        else:
                            grid_power[0] = grid_ac.getRegister(0)
                        if grid_ac.getRegister(1)>32767:
                            grid_power[1] = grid_ac.getRegister(1)-65535
                        else:
                            grid_power[1] = grid_ac.getRegister(1)
                        if grid_ac.getRegister(2)>32767:
                            grid_power[2] = grid_ac.getRegister(2)-65535
                        else:
                            grid_power[2] = grid_ac.getRegister(2)
                        
                        battery_acvc = client.read_holding_registers(26,2,unit=246)
                        
                        battery_voltage = battery_acvc.getRegister(0)
                        
                        battery_current = battery_acvc.getRegister(1)
                        
                        
                        print grid_power
                        
                        print "Vittoria"
                        time_check=1
                    
                        conn_status = True
                        # print("connected")
                

                
                        print grid_power
                    
                    except Exception:
                        print "error"
                        Pinst = 0
                        conn_status = False
                        grid_power = [0,0,0]
        
                else:
                    Pinst=0
                    conn_status = False
                    time_check=1
                    conn_to_ccgx = False
                    
            except Exception:
                    print "error"
                    Pinst = 0
                    conn_status = False
                    # conn_to_ccgx = False
                    grid_power = [0,0,0]
                    time_check=1
                          
        else:
            time_check=time_check+1
            Pinst = 0
            # conn_to_ccgx = False
            

            
        seconds = seconds + 1
        # Pinst = 30*10        #decomment ONLY for debug
        # conn_status = True #decomment ONLY for debug
        # seconds = seconds + 1 #decomment ONLY for debug
        Pinst = Pinst*10
        
        client.close()
        
        if (seconds % 10 == 0):
            with open("log.txt", "a") as myfile:
                data = [energie,Pinst,seconds]
                myfile.write(str(seconds) + "\t" + str(energie) + "\t" + str(Pinst) + "\t" + str(state_of_charge) + "\t" + str(conn_status) + "\t" + str(grid_power[0]) + "\t" + str(grid_power[1]) + "\t" + str(grid_power[2]) + "\t" + str(state)   + "\t" + str(battery_alarm) + "\t" + str(battery_voltage) + "\t" + str(battery_current) + "\t" + str(conn_to_ccgx)  + "\n")
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                # string = 'INSERT INTO sql11172989.Nuvola ' + '(Seconds, Energy, Pinst, StateOfCharge, ConnStatus, GridPower1, GridPower2, GridPower3, State, BatteryAlarm, Date) VALUES (' + str(seconds) + " , " + str(energie) + " , " + str(Pinst) + " , " + str(state_of_charge) + " , " + str(conn_status) + " , " + str(grid_power[0]) + " , " + str(grid_power[1]) + " , " + str(grid_power[2]) + " , " + str(state)   + " , " + str(battery_alarm) + ' , ' + str(timestamp) + ')'
                # print string
            try:
        
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                db = MySQLdb.connect(host="nuvolino.mysql.database.azure.com",    # your host, usually localhost
                                 user="nuvolino@nuvolino",         # your username
                                 passwd="RossiniEnergy123",  # your password
                                 db="sql11172989",
                                 connect_timeout = 3) 
                cur = db.cursor()
                cur.execute('INSERT INTO sql11172989.'+ table+ ' ' + 
                '(Seconds, Energy, Pinst, StateOfCharge, ConnStatus, GridPower1, GridPower2, GridPower3, State, BatteryAlarm, BatteryVoltage, BatteryCurrent, ConnCCGX, Date_) '
                'VALUES (' + str(seconds) + " , " + str(energie) + " , " + str(Pinst) + " , " + str(state_of_charge) + " , " + str(conn_status) + " , " + str(grid_power[0]) + " , " + str(grid_power[1]) + " , " + str(grid_power[2]) + " , " + str(state)   + " , " + str(battery_alarm) + " , " + str(battery_voltage) + " , " + str(battery_current) + " , " + str(conn_to_ccgx)  + ' , "' + str(timestamp) + '")'               )
                print ("sto scrivendo....")

                cur.close()
                db.commit()
                connect_to_db = True
                
            except Exception:
                connect_to_db = False
                print "Impossible to write to DB"
            
#rr = 2	    
        if Pinst > 0:
            energie += Pinst/3600000.0
#rr = client.read_holding_registers(2700, 3, unit=0)
        print(energie/1)
        #THIS WILL BE WRITTEN TOGETHER WITH backup3/5!! Every second!

            # print "Error %d: %s" % (e.args[0],e.args[1])

        data = [energie,Pinst,seconds]
        call(["cp","backup3.p","backup5.p"])
        write = open('backup3.p', 'wb')
        pickle.dump(data, write )
        client.close()

	#self.energy.text = str(round(energie/3600000.0,3))+" kWh"
	#self.euros.text = str(round(energie/3600000.0*0.15,3))+" eur"
	# client.close()
	#print("disconnected")

        # print "There was an exception"
        client.close()
        
    def on_stop(self):
	# energie = 12 #What is this???
	print seconds
	data = [energie,Pinst,seconds]
	print "Savage.. " 
	print data
	write = open('backup3.p', 'wb')
    
	pickle.dump(data, write )

if __name__ == '__main__':
   
   MyApp().run()
