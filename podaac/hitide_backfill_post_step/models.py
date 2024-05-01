"""Models file for backfilling database"""


from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, func

Base = declarative_base()


class StepExecution(Base):  # pylint: disable=too-few-public-methods
    """Model class for latest forge/tig step execution for a granule"""

    __tablename__ = 'step_execution'

    execution_name = Column(String(64), primary_key=True)
    granule = Column(String(128), ForeignKey("granule.cmr_concept_id"))
    cli_execution = Column(String(64), ForeignKey("cli_execution.uuid"))
    sf_type = Column(String(16))
    status = Column(String(16))
    execution_start = Column(DateTime(timezone=True))
    execution_stop = Column(DateTime(timezone=True))


class Granule(Base):  # pylint: disable=too-few-public-methods
    """Model class for data about a granule process through backfilling"""

    __tablename__ = 'granule'

    cmr_concept_id = Column(String(128), primary_key=True)
    collection_short_name = Column(String(128))
    collection_version = Column(String(16))
    granule_id = Column(String(128))
    granule_start = Column(DateTime(timezone=True))
    granule_end = Column(DateTime(timezone=True))


# pylint: disable=not-callable
class CliExecutions(Base):  # pylint: disable=too-few-public-methods
    """Model class for cli execution command"""

    __tablename__ = 'cli_execution'

    uuid = Column(String(64), primary_key=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    username = Column(String(32), nullable=True)
    collection_short_name = Column(String(128))
    collection_version = Column(String(16))
    cmr_search_start = Column(DateTime(timezone=True), nullable=True)
    cmr_search_end = Column(DateTime(timezone=True), nullable=True)
    tig_success = Column(Integer, default=0)
    tig_fails = Column(Integer, default=0)
    forge_success = Column(Integer, default=0)
    forge_fails = Column(Integer, default=0)
    dmrpp_success = Column(Integer, default=0)
    dmrpp_fails = Column(Integer, default=0)
    needs_recount = Column(Boolean, default=False)
