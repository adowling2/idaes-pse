##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes".
##############################################################################
"""
Standard IDAES CSTR model.
"""
from __future__ import division

# Import Pyomo libraries
# from pyomo.environ import Reals,  Var, NonNegativeReals
from pyomo.common.config import ConfigBlock, ConfigValue, In

# Import IDAES cores
from idaes.core import (ControlVolume0D,
                        declare_process_block_class,
                        MaterialBalanceType,
                        EnergyBalanceType,
                        MomentumBalanceType,
                        UnitBlockData,
                        useDefault)
from idaes.core.util.config import (is_physical_parameter_block,
                                    is_reaction_parameter_block,
                                    list_of_strings)
from idaes.core.util.misc import add_object_reference

__author__ = ""


@declare_process_block_class("CSTR")
class CSTRData(UnitBlockData):
    """
    Standard CSTR Unit Model Class
    """
    CONFIG = ConfigBlock()
    CONFIG.declare("dynamic", ConfigValue(
        domain=In([False]),
        default=False,
        description="Dynamic model flag - must be False",
        doc="""Ideal CSTRs do not support dynamic models, thus this must be
False."""))
    CONFIG.declare("has_holdup", ConfigValue(
        default=False,
        domain=In([True, False]),
        description="Holdup construction flag",
        doc="""Indicates whether holdup terms should be constructed or not.
Must be True if dynamic = True,
**default** - False.
**Valid values:** {
**True** - construct holdup terms,
**False** - do not construct holdup terms}"""))
    CONFIG.declare("material_balance_type", ConfigValue(
        default=MaterialBalanceType.componentPhase,
        domain=In(MaterialBalanceType),
        description="Material balance construction flag",
        doc="""Indicates what type of material balance should be constructed,
**default** - MaterialBalanceType.componentPhase.
**Valid values:** {
**MaterialBalanceType.none** - exclude material balances,
**MaterialBalanceType.componentPhase** - use phase component balances,
**MaterialBalanceType.componentTotal** - use total component balances,
**MaterialBalanceType.elementTotal** - use total element balances,
**MaterialBalanceType.total** - use total material balance.}"""))
    CONFIG.declare("energy_balance_type", ConfigValue(
        default=EnergyBalanceType.enthalpyTotal,
        domain=In(EnergyBalanceType),
        description="Energy balance construction flag",
        doc="""Indicates what type of energy balance should be constructed,
**default** - EnergyBalanceType.enthalpyTotal.
**Valid values:** {
**EnergyBalanceType.none** - exclude energy balances,
**EnergyBalanceType.enthalpyTotal** - single ethalpy balance for material,
**EnergyBalanceType.enthalpyPhase** - ethalpy balances for each phase,
**EnergyBalanceType.energyTotal** - single energy balance for material,
**EnergyBalanceType.energyPhase** - energy balances for each phase.}"""))
    CONFIG.declare("momentum_balance_type", ConfigValue(
        default=MomentumBalanceType.pressureTotal,
        domain=In(MomentumBalanceType),
        description="Momentum balance construction flag",
        doc="""Indicates what type of momentum balance should be constructed,
**default** - MomentumBalanceType.pressureTotal.
**Valid values:** {
**MomentumBalanceType.none** - exclude momentum balances,
**MomentumBalanceType.pressureTotal** - single pressure balance for material,
**MomentumBalanceType.pressurePhase** - pressure balances for each phase,
**MomentumBalanceType.momentumTotal** - single momentum balance for material,
**MomentumBalanceType.momentumPhase** - momentum balances for each phase.}"""))
    CONFIG.declare("has_heat_transfer", ConfigValue(
        default=False,
        domain=In([True, False]),
        description="Heat transfer term construction flag",
        doc="""Indicates whether terms for heat transfer should be constructed,
**default** - False.
**Valid values:** {
**True** - include heat transfer terms,
**False** - exclude heat transfer terms.}"""))
    CONFIG.declare("has_pressure_change", ConfigValue(
        default=False,
        domain=In([True, False]),
        description="Pressure change term construction flag",
        doc="""Indicates whether terms for pressure change should be
constructed,
**default** - False.
**Valid values:** {
**True** - include pressure change terms,
**False** - exclude pressure change terms.}"""))
    CONFIG.declare("has_equilibrium_reactions", ConfigValue(
        default=True,
        domain=In([True, False]),
        description="Equilibrium reaction construction flag",
        doc="""Indicates whether terms for equilibrium controlled reactions
should be constructed,
**default** - True.
**Valid values:** {
**True** - include equilibrium reaction terms,
**False** - exclude equilibrium reaction terms.}"""))
    CONFIG.declare("has_heat_of_reaction", ConfigValue(
        default=False,
        domain=In([True, False]),
        description="Heat of reaction term construction flag",
        doc="""Indicates whether terms for heat of reaction terms should be
constructed,
**default** - False.
**Valid values:** {
**True** - include heat of reaction terms,
**False** - exclude heat of reaction terms.}"""))
    CONFIG.declare("property_package", ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description="Property package to use for control volume",
        doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PropertyParameterObject** - a PropertyParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing property packages",
        doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))
    CONFIG.declare("reaction_package", ConfigValue(
        default=None,
        domain=is_reaction_parameter_block,
        description="Reaction package to use for control volume",
        doc="""Reaction parameter object used to define reaction calculations,
**default** - None.
**Valid values:** {
**None** - no reaction package,
**ReactionParameterBlock** - a ReactionParameterBlock object.}"""))
    CONFIG.declare("reaction_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing reaction packages",
        doc="""A ConfigBlock with arguments to be passed to a reaction block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see reaction package for documentation.}"""))
    CONFIG.declare("inlet_list", ConfigValue(
        domain=list_of_strings,
        description="List of inlet names",
        doc="""A list containing names of inlets (default = None)
                - None - default single inlet
                - list - a list of names for inlets"""))
    CONFIG.declare("num_inlets", ConfigValue(
        domain=int,
        description="Number of inlets to unit",
        doc="""Argument indication number (int) of inlets to construct
            (default = None). Not used if inlet_list arg is provided.
                - None - use inlet_list arg instead
                - int - Inlets will be named with sequential numbers from 1
                        to num_inlets"""))
    CONFIG.declare("outlet_list", ConfigValue(
        domain=list_of_strings,
        description="List of outlet names",
        doc="""A list containing names of outlets (default = None)
                - None - default single outlet
                - list - a list of names for outlets"""))
    CONFIG.declare("num_outlets", ConfigValue(
        domain=int,
        description="Number of outlets to unit",
        doc="""Argument indication number (int) of outlets to construct
            (default = None). Not used if outlet_list arg is provided.
                - None - use outlet_list arg instead
                - int - Outlets will be named with sequential numbers from 1
                        to num_outlets"""))

    def build(self):
        """
        Begin building model (pre-DAE transformation).
        Args:
            None
        Returns:
            None
        """
        # Call UnitModel.build to setup dynamics
        super(CSTRData, self).build()

        # Build Control Volume
        self.control_volume = ControlVolume0D(default={
                "dynamic": self.config.dynamic,
                "has_holdup": self.config.has_holdup,
                "property_package": self.config.property_package,
                "property_package_args": self.config.property_package_args,
                "reaction_package": self.config.reaction_package,
                "reaction_package_args": self.config.reaction_package_args})

        self.control_volume.add_geometry()

        self.control_volume.add_state_blocks()

        self.control_volume.add_reaction_blocks(
                has_equilibrium=self.config.has_equilibrium_reactions)

        self.control_volume.add_material_balances(
            balance_type=self.config.material_balance_type,
            has_rate_reactions=True,
            has_equilibrium_reactions=self.config.has_equilibrium_reactions)

        self.control_volume.add_energy_balances(
            balance_type=self.config.energy_balance_type,
            has_heat_of_reaction=self.config.has_heat_of_reaction,
            has_heat_transfer=self.config.has_heat_transfer)

        self.control_volume.add_momentum_balances(
            balance_type=self.config.momentum_balance_type,
            has_pressure_change=self.config.has_pressure_change)

        self.control_volume.add_total_pressure_balances(
            has_pressure_change=self.config.has_pressure_change)

        # Add Ports
        self.add_inlet_port()
        self.add_outlet_port()

        # Add object references
        add_object_reference(self,
                             "component_list_ref",
                             self.control_volume.component_list_ref)
        add_object_reference(self,
                             "phase_list_ref",
                             self.control_volume.phase_list_ref)
        add_object_reference(self,
                             "volume",
                             self.control_volume.volume)
        add_object_reference(self,
                             "rate_reaction_idx_ref",
                             self.control_volume.rate_reaction_idx_ref)

        # Add CSTR performance equation
        @self.Constraint(self.time_ref,
                         self.rate_reaction_idx_ref,
                         doc="CSTR performance equation")
        def cstr_performance_eqn(b, t, r):
            return b.control_volume.rate_reaction_extent[t, r] == (
                            b.volume[t] *
                            b.control_volume.reactions[t].reaction_rate[r])

        # Set references to balance terms at unit level
        if (self.config.has_heat_transfer is True and
                self.config.energy_balance_type != EnergyBalanceType.none):
            add_object_reference(self, "heat_duty", self.control_volume.heat)

        if (self.config.has_pressure_change is True and
                self.config.momentum_balance_type != 'none'):
            add_object_reference(self, "deltaP", self.control_volume.deltaP)
