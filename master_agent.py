# master_agent.py
"""""
Master agent that controls PADE Device Agents.

"""

from pade.misc.utility import display_message
from pade.core.agent import Agent
from pade.drivers.mosaik_driver import MosaikCon

MOSAIK_MODELS = {
    'api_version': '3.0.2',
    'type': 'event-based',
    'models': {
        'MasterAgent': {
            'public': True,
            'params': [],
            'attrs': ['P_in', 'P_out', 'node_id'],  #TODO: ajustar configuração do master_agent - Dúvida: retirar node_id?
            # 'trigger': ['P'],   # trigger is a list of attribute names that cause the simulator to be stepped when another simulator provides output which is connected to one of those.
        },
    },
}

class MosaikSim(MosaikCon):
    def __init__(self, agent):
        super(MosaikSim, self).__init__(MOSAIK_MODELS, agent)
        self.master_sim_prefix = 'MasterSim0-0.MasterAgent_'
        self.agents = []
        self.data = {}
        self.cache = {} # armazena último valor obtido pelo DeviceAgent
        self.time = 0    # Dúvida: já está definido em MosaikSim, preciso definir novamente?  

    #TODO: ajustar init() do MasterAgent - deletar
    def init(self, sid, time_resolution, eid_prefix, prosumer_ref, start, step_size):
        # self.sid = sid
        self.prosumer_ref = 'MasterSim0-0.MasterAgent_{}'.format(prosumer_ref)
        self.node_id = prosumer_ref
        self.eid_prefix = eid_prefix
        self.eid = '{}-{}'.format(self.eid_prefix, prosumer_ref)
        self.start = start
        self.step_size = step_size
        return MOSAIK_MODELS

    def create(self, num, model='MasterAgent'):
        n_agents = len(self.agents) # already created agents
        self.entities = list()
        for i in range(n_agents, n_agents + num):
            self.entities.append(
                {'eid': self.eid, 'type': model})
        return self.entities

    def step(self, time, inputs, max_advance):
        print('inputs: {}'.format(inputs))
        self.time = time
        data = {}
        for agent_eid, attrs in inputs.items():
            values_dict = attrs.get('P_in', {})
            for key, value in values_dict.items():
                self.cache[key] = value
                print('key: {}'.format(key))
                print('value: {}'.format(value))
            if(value >= 200):
                data[agent_eid] = {'P_out': 200}

        self.data = data        
        print('cache: {}'.format(self.cache))
        #return time + self.step_size
        return None # Mosaik 3.0

    def handle_set_data(self):
        pass

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in MOSAIK_MODELS['models']['MasterAgent']['attrs']:
                    raise ValueError('Unknown output attribute: {}'.format(attr))
                data[eid][attr] = getattr(self, attr)
        return data

"""
Classe de inicialização dos agentes PADE

"""
class MasterAgent(Agent):
    def __init__(self, aid):
        super(MasterAgent, self).__init__(aid=aid, debug=False)
        #self.node_id = node_id
        self.mosaik_sim = MosaikSim(self)
        # self.dm_curve = np.zeros(50)
        # self.clear_price = None

        # open the config.json file with some important informations about
        # the device characteristics, read and store this information.
        # config = json.load(open('config.json'))

        '''This part of code create a dictionary like this:

            {'stochastic_gen': {'power': 5.41, 'status': None, 'demand': None},
            'shiftable_load': {'power': 2.02, 'status': None, 'demand': None},
            'buffering_device': {'power': 2.1, 'status': None, 'demand': None},
            'user_action_device': {'power': 5.55, 'status': None, 'demand': None}}

        
        self.device_dict = dict()
        for device_type, device_info in config['devices'].items():
            if str(self.node_id) in device_info['powers'].keys():
                self.device_dict[device_type] = {'power': device_info['powers'][str(self.node_id)],
                                                 'status': None,
                                                 'demand': None}
        '''
        #print(self.aid.name)
        #print('================== MASTER AGENT ATIVO')
        #print(self.device_dict)