import json
import os
from typing import List, Optional
from .agent import Agent
from datetime import datetime
from uuid import UUID

class AgentStore:
    def __init__(self):
        self.store_file = os.path.join(os.path.dirname(__file__), 'data', 'agents.json')
        self._ensure_data_directory()
        self._ensure_store_file()

    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)

    def _ensure_store_file(self):
        """Create the store file if it doesn't exist"""
        if not os.path.exists(self.store_file):
            with open(self.store_file, 'w') as f:
                json.dump([], f)

    def _load_agents(self) -> List[dict]:
        """Load agents from the JSON file"""
        with open(self.store_file, 'r') as f:
            return json.load(f)

    def _save_agents(self, agents: List[dict]):
        """Save agents to the JSON file"""
        with open(self.store_file, 'w') as f:
            json.dump(agents, f, indent=2, default=str)

    def get_all_agents(self) -> List[Agent]:
        """Retrieve all agents"""
        agents_data = self._load_agents()
        return [Agent(**agent) for agent in agents_data]

    def get_agent_by_id(self, agent_id: UUID) -> Optional[Agent]:
        """Retrieve an agent by ID"""
        agents = self._load_agents()
        agent = next((a for a in agents if a['id'] == str(agent_id)), None)
        return Agent(**agent) if agent else None

    def add_agent(self, agent: Agent) -> Agent:
        """Add a new agent"""
        agents = self._load_agents()
        agent_dict = agent.model_dump()
        agents.append(agent_dict)
        self._save_agents(agents)
        return agent

    def update_agent(self, agent_id: UUID, agent_data: dict) -> Optional[Agent]:
        """Update an existing agent"""
        agents = self._load_agents()
        for i, agent in enumerate(agents):
            if agent['id'] == str(agent_id):
                agents[i].update(agent_data)
                agents[i]['updated_at'] = datetime.utcnow().isoformat()
                self._save_agents(agents)
                return Agent(**agents[i])
        return None

    def delete_agent(self, agent_id: UUID) -> bool:
        """Delete an agent"""
        agents = self._load_agents()
        initial_length = len(agents)
        agents = [a for a in agents if a['id'] != str(agent_id)]
        if len(agents) != initial_length:
            self._save_agents(agents)
            return True
        return False
