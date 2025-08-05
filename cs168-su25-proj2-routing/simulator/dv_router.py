"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import (
    RoutePacket,
    Table,
    TableEntry,
    DVRouterBase,
    Ports,
    FOREVER,
    INFINITY,
)


class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = True
    POISON_REVERSE = False
    # -----------------------------------------------

    # Determines if you send poison for expired routes
    POISON_EXPIRED = False

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False
    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (
            self.SPLIT_HORIZON and self.POISON_REVERSE
        ), "Split horizon and poison reverse can't both be on"

        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()
        # This is the table that contains all current routes
        self.table = Table()
        self.table.owner = self
        ##### Begin Stage 10A #####
        self.history = {}

        ##### End Stage 10A #####

    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."

        ##### Begin Stage 1 #####
        self.table[host] = TableEntry(dst=host , port=port ,latency=0.1 ,expire_time=FOREVER)
        ##### End Stage 1 #####

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        
        ##### Begin Stage 2 #####
        if packet.dst  in self.table and self.table[packet.dst].latency < INFINITY:
            self.send(packet , self.table[packet.dst].port)
        ##### End Stage 2 #####
    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        ##### Begin Stages 3, 6, 7, 8, 10 #####
        ports = []
        if single_port == None:
           ports = [port for port in self.ports.get_all_ports()]
        else:
           ports = [single_port]       
        for port in ports:
            for key in self.table.keys():
                if self.table[key].latency > self.ROUTE_TTL:
                    if force == True:
                        self.send_route(port , key , INFINITY)
                    else :
                        if key not in self.history.keys() or self.history[key][0] != self.table[key].latency:
                            self.send_route(port , key , INFINITY )
                    continue
                if self.SPLIT_HORIZON == True and self.table[key].port == port :
                   continue 
                if self.POISON_REVERSE == True and self.table[key].port == port:
                    if force == True:
                        self.send_route(port , key , INFINITY)
                    else :
                        if key not in self.history.keys():
                              self.send_route(port , key , INFINITY)
                        elif self.history[key][1] != port:
                              self.send_route(port , key , INFINITY)
                else:
                    if force == True:
                        self.send_route(port , key , self.table[key].latency)
                    else:
                        if key not in self.history.keys() or self.history[key][0] != self.table[key].latency:
                            self.send_route(port , key , self.table[key].latency)
        for key in self.table.keys():
            self.history[key] = [self.table[key].latency , self.table[key].port]
        ##### End Stages 3, 6, 7, 8, 10 #####

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        ##### Begin Stages 5, 9 #####
        expire_list = []
        for key in self.table.keys():
            if self.table[key].expire_time -api.current_time() <= 0:
                expire_list.append(key)
            
        for item in expire_list:
            if self.POISON_EXPIRED:
                self.table[item] = TableEntry(dst=item,port=self.table[item].port,latency=INFINITY,expire_time=api.current_time() + self.ROUTE_TTL)
            else:
                self.table.pop(item)
        ##### End Stages 5, 9 #####

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
     
        ##### Begin Stages 4, 10 #####
        if route_dst not in self.table.keys():
            self.table[route_dst] = TableEntry(dst=route_dst ,port=port,latency=route_latency + self.ports.get_latency(port),expire_time=api.current_time() + 15)
            self.send_routes(force=False)
            return 
        if  port == self.table[route_dst].port:
            self.table[route_dst] = TableEntry(dst=route_dst ,port=port,latency=route_latency+ self.ports.get_latency(port),expire_time=api.current_time() + 15)
            self.send_routes(force=False)
            return 
        if  route_latency + self.ports.get_latency(port) < self.table[route_dst].latency:
            self.table[route_dst] = TableEntry(dst=route_dst ,port=port,latency=route_latency + self.ports.get_latency(port),expire_time=api.current_time() + 15)
            self.send_routes(force=False)
        ##### End Stages 4, 10 #####

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        ##### Begin Stage 10B #####
        if self.SEND_ON_LINK_UP:
            self.send_routes(force=False , single_port=port)
        ##### End Stage 10B #####

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router goes down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        ##### Begin Stage 10B #####
        if self.POISON_ON_LINK_DOWN:
           for key in self.table.keys():
               if self.table[key].port == port:
                   self.table[key] = TableEntry(dst=self.table[key].dst ,port =port , latency= INFINITY , expire_time=api.current_time() + self.ROUTE_TTL)
                   self.send_routes(force=False)
        else:
           items = []
           for key in self.table.keys():
               if self.table[key].port == port:
                  items.append(key)
           for item in items:
                self.table.pop(item)
            ##### End Stage 10B #####

    # Feel free to add any helper methods!
