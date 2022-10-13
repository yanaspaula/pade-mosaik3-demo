#!coding=utf-8
# Hello world in PADE!
#
# Criado por Lucas S Melo em 21 de julho de 2015 - Fortaleza, Ceará - Brasil

from pade.misc.utility import display_message
from pade.core.agent import Agent
from pade.drivers.mosaik_driver import MosaikCon

import pandas as pd
import numpy as np
import json
import pickle
import random

MOSAIK_MODELS = {
    'api_version': '3.0', # DOCUMENTATION: Since mosaik API version 2.2, the simulator’s major version (“x”, in the snippet above) has to be equal to mosaik’s. Mosaik will cancel the simulation if a version mismatch occurs.
    'type': 'event-based', # Mosaik 3.0: Component's type
    # DOCUMENTATION: Time-based simulators only decide themselves on which points in time they want to be stepped (i.e. communicate with the other simulators). Their output is valid until the next step.
    # DOCUMENTATION: Event-based simulators are always stepped when a predecessor provides new input, but they can also schedule steps for themselves. 
    'models': {
        'DeviceAgent': {
            'public': True,
            'params': [],
            'attrs': ['P', 'node_id'],
        },
    },
}


class MosaikSim(MosaikCon): # Dúvida: onde posso acessar a classe mosaik_api.Simulator para comparar com a classe mosaik_driver.MosaikCon?

    def __init__(self, agent): # Dúvida: onde está o step_size? No mosaik_driver -> posso retirar?
        super(MosaikSim, self).__init__(MOSAIK_MODELS, agent)
        self.prosumer_sim_prefix = 'ProsumerSim0-0.Prosumer_'
        self.prosumer_data = {'stochastic_gen': [],
                              'freely_control_gen': [],
                              'shiftable_load': [],
                              'buffering_device': [],
                              'user_action_device': [],
                              'storage_device': []}
        self.P = 100.0      # Dúvida: o que é isso?

    # def init(self, sid, eid_prefix, prosumer_ref, start, step_size): # Mosaik 2.0
    def init(self, sid, time_resolution, eid_prefix, prosumer_ref, start): # Mosaik 3.0: Time resolution
        # Dúvida: o que fazer com o time_resolution? Como tratá-lo???
        # self.sid = sid
        self.prosumer_ref = 'ProsumerSim0-0.Prosumer_{}'.format(prosumer_ref)
        self.node_id = prosumer_ref
        self.eid_prefix = eid_prefix
        self.eid = '{}-{}'.format(self.eid_prefix, prosumer_ref)
        self.start = start
        # self.step_size = step_size # Mosaik 2.0       # Dúvida: como refletir no mosaik_driver?
        return MOSAIK_MODELS


    def create(self, num, model):
        self.entities = list()
        # self.eid = '{}0'.format(self.eid_prefix)
        self.entities.append(
            #{'eid': self.sim_id + '.' + str(i), 'type': model, 'rel': []})
            {'eid': self.eid, 'type': 'DeviceAgent'})
        return self.entities

    # def step(self, time, inputs): # Mosaik 2.0
    def step(self, time, inputs, max_advance): # Mosaik 3.0: Max_advance time
        '''
        {'DeviceAgent_10': 
            {'device_status': 
                {'ProsumerSim0-0.Prosumer_10': 
                    {'stochastic_gen': {'status': 0, 'demand': 0.0, 'forecast': 0.0},
                     'freely_control_gen': {'status': 0, 'demand': 0.0, 'forecast': 0.0},
                     'shiftable_load': {'status': 0, 'demand': 0.0, 'forecast': 0.0},
                     'buffering_device': {'status': 0, 'demand': 0.0, 'forecast': 0.0},
                     'user_action_device': {'status': 1, 'demand': 0.0649, 'forecast': 0.0},
                     'storage_device': {'status': 1, 'demand': 0.0, 'forecast': 0.0}
                    }
                }
            }
        }
        '''
        # print(inputs)
        if time % (1 * 60) == 0 and time != 0: # a cada 5 min # Dúvida: o que fazer com isso????
            # =================================================
            # armazenamento dos parâmetros vindos do Mosaik
            # No momento apenas: staus e demanda.
            # =================================================

            for eid, attrs in inputs.items():
                P = attrs.get('P', {})
                for prosumer_eid, P_ in P.items():
                    pass
                    self.P = P_ * 0.1
                    # print(P_)
            # =================================================
            # envio de comandos para os dispositivos modelados
            # no Mosaik
            # =================================================

            # from_ = self.eid
            # to_ = self.prosumer_ref
            # data = {from_: {to_: {'commands': self.agent.device_dict}}}
            # yield self.set_data_async(data)
            
        ###################### FIX #############################

        # armazena os dados da simulação
        if time % (1 * 24 * 60 * 60) == 0 and time != 0: # a cada dois dias
            pass

        #return time + self.step_size # Mosaik 2.0
        return None # Mosaik 3.0            # Dúvida: como refletir no mosaik_driver?

    def handle_set_data(self):
        pass

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in MOSAIK_MODELS['models']['DeviceAgent']['attrs']:
                    raise ValueError('Unknown output attribute: {}'.format(attr))
                data[eid][attr] = getattr(self, attr)
        return data


class DeviceAgent(Agent):
    def __init__(self, aid, node_id):
        super(DeviceAgent, self).__init__(aid=aid, debug=False)
        self.node_id = node_id
        self.mosaik_sim = MosaikSim(self)
        self.dm_curve = np.zeros(50)
        self.clear_price = None

        # opens config.json file with some important informations about
        # the device characteristics, reads and stores this information.
        config = json.load(open('config.json'))

        '''This part of code creates a dictionary like this:

            {'stochastic_gen': {'power': 5.41, 'status': None, 'demand': None},
            'shiftable_load': {'power': 2.02, 'status': None, 'demand': None},
            'buffering_device': {'power': 2.1, 'status': None, 'demand': None},
            'user_action_device': {'power': 5.55, 'status': None, 'demand': None}}

        '''
        self.device_dict = dict()
        for device_type, device_info in config['devices'].items():
            if str(self.node_id) in device_info['powers'].keys():
                self.device_dict[device_type] = {'power': device_info['powers'][str(self.node_id)],
                                                 'status': None,
                                                 'demand': None}
        # print(self.aid.name)
        # print(self.device_dict)