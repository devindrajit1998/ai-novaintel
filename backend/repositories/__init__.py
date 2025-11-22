"""
Repository pattern for data access layer.
"""
from repositories.base_repository import BaseRepository
from repositories.proposal_repository import ProposalRepository
from repositories.project_repository import ProjectRepository

__all__ = [
    "BaseRepository",
    "ProposalRepository",
    "ProjectRepository",
]

