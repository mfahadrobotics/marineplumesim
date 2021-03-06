import numpy
import matplotlib
matplotlib.use ( 'Agg' )
import matplotlib.pyplot as plt
from xml.dom import minidom
from math import ceil
from math import sqrt
from math import atan2
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray
import rospy
from tf.transformations import quaternion_from_euler
from tempfile import TemporaryFile

class flow():
    
    def __init__(self):
        xmldoc = minidom.parse('sim_properties.xml')
        
        itemlist = xmldoc.getElementsByTagName('lx')
        self.lx=float(itemlist[0].attributes['val'].value)
        itemlist = xmldoc.getElementsByTagName('ly')
        self.ly=float(itemlist[0].attributes['val'].value)
        
        itemlist = xmldoc.getElementsByTagName('grid_x')
        self.dx=float(itemlist[0].attributes['val'].value)
        itemlist = xmldoc.getElementsByTagName('grid_y')
        self.dy=float(itemlist[0].attributes['val'].value)
        
        itemlist = xmldoc.getElementsByTagName('sim_duration')
        self.sim_duration=float(itemlist[0].attributes['val'].value)
        print str(self.sim_duration)
        
        itemlist = xmldoc.getElementsByTagName('flow_up_rt')
        self.flow_up_rt=float(itemlist[0].attributes['val'].value)
        
        itemlist = xmldoc.getElementsByTagName('flow_x')
        self.v1_x_max=float(itemlist[0].attributes['val'].value)
        self.v1_x_dir=str(itemlist[0].attributes['chg_dir'].value)
        itemlist = xmldoc.getElementsByTagName('flow_y')
        self.v1_y_max=float(itemlist[0].attributes['val'].value)
        self.v1_y_dir=str(itemlist[0].attributes['chg_dir'].value)      
                
        self.no_of_iter = int(ceil(self.sim_duration/self.flow_up_rt))
        
        self.markerArray = MarkerArray()
        
        self.nx=int(ceil(self.lx/self.dx))
        self.ny=int(ceil(self.ly/self.dy))
        itemlist = xmldoc.getElementsByTagName('flow_sol_t')
        self.nt = int(itemlist[0].attributes['val'].value)
        itemlist = xmldoc.getElementsByTagName('flow_p_nit')
        self.nit = int(itemlist[0].attributes['val'].value)
        
        self.rho = 1.0
        self.nu = 0.1
        self.dt = 0.001
        
        self.x = numpy.linspace ( 0.0, self.lx, self.nx )
        self.y = numpy.linspace ( 0.0, self.ly, self.ny )
        self.X, self.Y = numpy.meshgrid ( self.x, self.y )
        self.u = numpy.zeros((self.ny, self.nx))
        self.v = numpy.zeros((self.ny, self.nx))
        self.p = numpy.zeros((self.ny, self.nx))
        self.un = numpy.zeros((self.ny, self.nx))
        self.vn = numpy.zeros((self.ny, self.nx))
        self.b = numpy.zeros ( ( self.ny, self.nx ) )
        
        self.flow_upd()
       
    def buildUpB (self):
        
      self.b[1:-1,1:-1] = self.rho * ( 1.0 / self.dt * \
        ( ( self.u[1:-1,2:] - self.u[1:-1,0:-2] ) / ( 2 * self.dx ) \
        + ( self.v[2:,1:-1] - self.v[0:-2,1:-1] ) / ( 2 * self.dy ) ) \
        - ( ( self.u[1:-1,2:] - self.u[1:-1,0:-2] ) / ( 2 * self.dx ) ) ** 2 \
        - 2 * ( ( self.u[2:,1:-1] - self.u[0:-2,1:-1] ) / ( 2 * self.dy ) \
              * ( self.v[1:-1,2:] - self.v[1:-1,0:-2] ) / ( 2 * self.dx ) ) \
        - ( ( self.v[2:,1:-1] - self.v[0:-2,1:-1] ) / ( 2 * self.dy ) ) ** 2 )
    

    def presPoisson (self):
    
      self.pn = self.p.copy ( )
        
      for q in range ( self.nit ):
    
        self.pn = self.p.copy ( )
    
        self.p[1:-1,1:-1] = ( ( self.pn[1:-1,2:] + self.pn[1:-1,0:-2] ) * self.dy ** 2 \
                       + ( self.pn[2:,1:-1] + self.pn[0:-2,1:-1] ) * self.dx ** 2 ) \
                       / ( 2.0 * ( self.dx ** 2 + self.dy ** 2 ) ) \
                       - self.dx ** 2 * self.dy ** 2 \
                       / ( 2.0 * ( self.dx ** 2 + self.dy ** 2 ) ) * self.b[1:-1,1:-1]
    
        self.p[:,-1] = self.p[:,-2]
        self.p[0,:] = self.p[1,:]
        self.p[:,0] = self.p[:,1]
        self.p[-1,:] = 0.0

    def cavityFlow (self ):
       
      for n in range ( self.nt ):
    
        self.un = self.u.copy ( )
        self.vn = self.v.copy ( )
            
        self.buildUpB()
    
        self.presPoisson()
            
        self.u[1:-1,1:-1] = self.un[1:-1,1:-1] \
          - self.un[1:-1,1:-1] * self.dt / self.dx * ( self.un[1:-1,1:-1] - self.un[1:-1,0:-2] ) \
          - self.vn[1:-1,1:-1] * self.dt / self.dy * ( self.un[1:-1,1:-1] - self.un[0:-2,1:-1] ) \
          - self.dt / ( 2 * self.rho * self.dx ) * ( self.p[1:-1,2:] - self.p[1:-1,0:-2] ) \
          + self.nu * ( self.dt / self.dx ** 2 * ( self.un[1:-1,2:] - 2 * self.un[1:-1,1:-1] + self.un[1:-1,0:-2] ) \
                 + self.dt / self.dy ** 2 * ( self.un[2:,1:-1] - 2 * self.un[1:-1,1:-1] + self.un[0:-2,1:-1] ) )
    
        self.v[1:-1,1:-1] = self.vn[1:-1,1:-1] \
          - self.un[1:-1,1:-1]*self.dt/self.dx*(self.vn[1:-1,1:-1]-self.vn[1:-1,0:-2]) \
          - self.vn[1:-1,1:-1]*self.dt/self.dy*(self.vn[1:-1,1:-1]-self.vn[0:-2,1:-1]) \
          - self.dt/(2*self.rho*self.dy)*(self.p[2:,1:-1]-self.p[0:-2,1:-1]) \
          + self.nu*(self.dt/self.dx**2*(self.vn[1:-1,2:]-2*self.vn[1:-1,1:-1]+self.vn[1:-1,0:-2])\
               +self.dt/self.dy**2*(self.vn[2:,1:-1]-2*self.vn[1:-1,1:-1]+self.vn[0:-2,1:-1]))
    
        self.u[0,:] = self.bf_x #bottom wall
        self.v[0,:] = self.bf_y #bottom wall 
        
        self.u[:,0] = self.lf_x #left wall
        self.v[:,0] = self.lf_y #left wall
        
        self.u[:,-1] = self.rf_x #right wall
        self.v[:,-1] = self.rf_y #right wall
        
        self.u[-1,:] = self.tf_x #top wall
        self.v[-1,:] = self.tf_y #top wall

    def flow_upd(self):
        if self.v1_x_dir=="Y":
            self.bf_x = self.v1_x_max*numpy.random.uniform(-1,1) #bottom wall
        else:
            self.bf_x = self.v1_x_max*abs(numpy.random.random()) #bottom wall
        
        if self.v1_y_dir=="Y":
            self.bf_y = self.v1_y_max*numpy.random.uniform(-1,1)#bottom wall
        else:
            self.bf_y = self.v1_y_max*abs(numpy.random.random()) #bottom wall

        if self.v1_x_dir=="Y":
            self.lf_x = self.v1_x_max*numpy.random.uniform(-1,1) #left wall
        else:
            self.lf_x = self.v1_x_max*abs(numpy.random.random()) #left wall
        
        if self.v1_y_dir=="Y":
            self.lf_y = self.v1_y_max*numpy.random.uniform(-1,1)#left wall
        else:
            self.lf_y = self.v1_y_max*abs(numpy.random.random()) #left wall

        self.rf_x = self.lf_x
        self.rf_y = self.lf_y
        self.tf_x = self.bf_x
        self.tf_y = self.bf_y


    def ros_pub_setup(self):
        rospy.init_node('flow_pub')
        self.marker_array_pub = rospy.Publisher('flow_cld', MarkerArray, queue_size=10)
        rospy.sleep(1.0)

    def save(self,af):
        u_fname = 'data/u'+str(af)+'_save.npy'
        v_fname = 'data/v'+str(af)+'_save.npy'
        numpy.save(u_fname,self.u)
        numpy.save(v_fname,self.v)

if __name__ == '__main__':
    flow_chk = flow()  
    for af in range (0,flow_chk.no_of_iter):
        flow_chk.flow_upd()
        flow_chk.cavityFlow()
        print str(af)
        flow_chk.save(af)


