import serial
import numpy
import matplotlib.pyplot as plot
from collections import deque
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MultipleLocator
from matplotlib.widgets import CheckButtons
ser= serial.Serial('COM4',115200)
list_ch0= deque(maxlen=100)
list_ch1= deque(maxlen=100)
fig,ax=plot.subplots()
fig.subplots_adjust(left=0.22,top=0.82)
rax=fig.add_axes([0.02,0.78,0.15,0.12])
check=CheckButtons(rax,('Channel 1' , 'Channel 2'),(True,True))

pause= False
def keypress(event):
    global pause
    if event.key==' ':
        pause= not pause
        if pause:
            fig.canvas.manager.set_window_title('PAUSED')
        else:
            fig.canvas.manager.set_window_title('LIVE')
fig.canvas.mpl_connect('key_press_event' , keypress)   

def update(frame):

    global pause
    if not pause:
        while ser.in_waiting>0 :
            line= ser.readline().decode('utf-8' , errors='ignore').strip()
            parts= line.split(',')
            if len(parts)==2:
                try:
                    A0= float(parts[0])
                    A1= float(parts[1])
                    VA0= (A0/1023)*5
                    VA1= (A1/1023)*5
                    Vp0=(VA0-2.444)/0.104
                    Vp1=(VA1-2.479)/0.105
                    list_ch0.append(Vp0)
                    list_ch1.append(Vp1)
                except ValueError:
                    continue
    ax.cla()
    status= check.get_status()
    if status[0] and len(list_ch0)>0:
        ax.plot(list_ch0 , label="Channel 1" , color='tab:blue')
        arr0=numpy.array(list_ch0)
        Vmax0=numpy.max(arr0)
        Vmin0=numpy.min(arr0)
        Vpp0=Vmax0-Vmin0
        Vrms0=numpy.sqrt(numpy.mean(arr0**2))
        text_ch1=f"CH1 Vpp={Vpp0:.2f}V  Vmax={Vmax0:.2f}V  Vmin={Vmin0:.2f}V  Vrms={Vrms0:.2f}V"
        fig.text(0.22,0.93,text_ch1,fontsize=9,fontfamily='monospace',color='tab:gray')
    if status[1] and len(list_ch1)>0:
        ax.plot(list_ch1 , label="Channel 2" , color='tab:orange')
        arr1=numpy.array(list_ch1)
        Vmax1=numpy.max(arr1)
        Vmin1=numpy.min(arr1)
        Vpp1=Vmax1-Vmin1
        Vrms1=numpy.sqrt(numpy.mean(arr1**2))
        text_ch2=f"CH2 Vpp={Vpp1:.2f}V  Vmax={Vmax1:.2f}V  Vmin={Vmin1:.2f}V  Vrms={Vrms1:.2f}V"
        fig.text(0.22,0.88,text_ch2,fontsize=9,fontfamily='monospace',color='tab:gray')
    while len(fig.texts)>2:
        fig.texts[0].remove()    
    ax.set_ylim(-22,22)
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.yaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(True, which='major' , color='gray' , linestyle='-' , linewidth=0.8)
    ax.grid(True, which='minor' , color='lightgray' , linestyle=':' , linewidth=0.5)       
    ax.set_xlabel("Sample")
    ax.set_ylabel("Magnitude (V)")
    ax.legend(loc="lower right")
animation=FuncAnimation(fig,update,interval=20,cache_frame_data=False)    
plot.show()
