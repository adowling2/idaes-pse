# -*- coding: utf-8 -*-
#################################################################################
# The Institute for the Design of Advanced Energy Systems Integrated Platform
# Framework (IDAES IP) was produced under the DOE Institute for the
# Design of Advanced Energy Systems (IDAES).
#
# Copyright (c) 2018-2024 by the software owners: The Regents of the
# University of California, through Lawrence Berkeley National Laboratory,
# National Technology & Engineering Solutions of Sandia, LLC, Carnegie Mellon
# University, West Virginia University Research Corporation, et al.
# All rights reserved.  Please see the files COPYRIGHT.md and LICENSE.md
# for full copyright and license information.
#################################################################################
"""
This module contains utility functions for reporting structural statistics of
IDAES models.
"""

__author__ = "Andrew Lee"

import sys

from pyomo.environ import Block, Constraint, Expression, Objective, Var, value
from pyomo.dae import DerivativeVar
from pyomo.core.expr import identify_variables
from pyomo.common.collections import ComponentSet
from pyomo.common.deprecation import deprecation_warning
from pyomo.contrib.pynumero.interfaces.external_grey_box import ExternalGreyBoxBlock

import idaes.logger as idaeslog

_log = idaeslog.getLogger(__name__)


# -------------------------------------------------------------------------
# Generator to handle cases where the input is an indexed Block
# Indexed blocks do not have component_data_objects, so we need to iterate
# over the indexed block first.
def _iter_indexed_block_data_objects(block, ctype, active, descend_into):
    if block.is_indexed():
        for bd in block.values():
            for c in bd.component_data_objects(
                ctype=ctype, active=active, descend_into=descend_into
            ):
                yield c
    else:
        for c in block.component_data_objects(
            ctype=ctype, active=active, descend_into=descend_into
        ):
            yield c


# -------------------------------------------------------------------------
# Block methods
def total_blocks_set(block):
    """
    Method to return a ComponentSet of all Block components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Block components in block (including block
        itself)
    """
    total_blocks_set = ComponentSet(
        _iter_indexed_block_data_objects(
            block, ctype=Block, active=None, descend_into=True
        )
    )
    total_blocks_set.add(block)
    return total_blocks_set


def number_total_blocks(block):
    """
    Method to return the number of Block components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Block components in block (including block itself)
    """
    # +1 to include main model
    return (
        sum(
            1
            for _ in _iter_indexed_block_data_objects(
                block, ctype=Block, active=None, descend_into=True
            )
        )
        + 1
    )


def activated_blocks_set(block):
    """
    Method to return a ComponentSet of all activated Block components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all activated Block components in block
        (including block itself)
    """
    block_set = ComponentSet()
    if block.active:
        block_set.add(block)
        for b in _iter_indexed_block_data_objects(
            block, ctype=Block, active=True, descend_into=True
        ):
            block_set.add(b)
    return block_set


def greybox_block_set(block):
    """
    Function to return ComponentSet of all Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all GreyBox Block components in block
        (including block itself)
    """
    block_set = ComponentSet()
    for grey_box in activated_block_component_generator(
        block, ctype=ExternalGreyBoxBlock
    ):
        block_set.add(grey_box)

    return block_set


def activated_greybox_block_set(block):
    """
    Function to return ComponentSet of activated Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all GreyBox Block components in block
        (including block itself)
    """
    block_set = ComponentSet()
    for grey_box in greybox_block_set(block):
        if grey_box.active:
            block_set.add(grey_box)

    return block_set


def deactivated_greybox_block_set(block):
    """
    Function to return ComponentSet of deactivated Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all GreyBox Block components in block
        (including block itself)
    """
    return greybox_block_set(block) - activated_greybox_block_set(block)


def number_deactivated_greybox_block(block):
    """
    Function to return a Number of deactivated Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        number of deactivated greybox blocks
    """
    return len(deactivated_greybox_block_set(block))


def number_greybox_blocks(block):
    """
    Function to return a number of Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        number of activated greybox blocks
    """
    return len(greybox_block_set(block))


def number_activated_greybox_blocks(block):
    """
    Function to return a Number of activated Greybox Blocks components in a
    model.

    Args:
        block : model to be studied

    Returns:
        number of activated greybox blocks
    """
    return len(activated_greybox_block_set(block))


def number_activated_blocks(block):
    """
    Method to return the number of activated Block components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of activated Block components in block (including block itself)
    """
    b = 0
    if block.active:
        b = 1
        b += sum(
            1
            for _ in _iter_indexed_block_data_objects(
                block, ctype=Block, active=True, descend_into=True
            )
        )
    return b


def deactivated_blocks_set(block):
    """
    Method to return a ComponentSet of all deactivated Block components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all deactivated Block components in block
        (including block itself)
    """
    # component_data_objects active=False does not seem to work as expected
    # Use difference of total and active block sets
    return total_blocks_set(block) - activated_blocks_set(block)


def number_deactivated_blocks(block):
    """
    Method to return the number of deactivated Block components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of deactivated Block components in block (including block
        itself)
    """
    # component_data_objects active=False does not seem to work as expected
    # Use difference of total and active block sets
    return number_total_blocks(block) - number_activated_blocks(block)


# -------------------------------------------------------------------------
# Basic Constraint methods
def total_constraints_set(block):
    """
    Method to return a ComponentSet of all Constraint components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Constraint components in block
    """
    return ComponentSet(activated_block_component_generator(block, ctype=Constraint))


def number_total_constraints(block):
    """
    Method to return the total number of Constraint components in a model.
    This will include the number of constraints provided by Greybox models using
    the number_activated_greybox_equalities function.

    Args:
        block : model to be studied

    Returns:
        Number of Constraint components in block
    """
    number_standard_constraints = sum(
        1 for _ in activated_block_component_generator(block, ctype=Constraint)
    )
    number_greybox_constraints = number_activated_greybox_equalities(block)
    return number_standard_constraints + number_greybox_constraints


def activated_constraints_generator(block):
    """
    Generator which returns all activated Constraint components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all activated Constraint components block
    """
    for c in activated_block_component_generator(block, ctype=Constraint):
        if c.active:
            yield c


def activated_constraints_set(block):
    """
    Method to return a ComponentSet of all activated Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all activated Constraint components in block
    """
    return ComponentSet(activated_constraints_generator(block))


def number_activated_constraints(block):
    """
    Method to return the number of activated Constraint components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of activated Constraint components in block
    """
    return sum(1 for _ in activated_constraints_generator(block))


def deactivated_constraints_generator(block):
    """
    Generator which returns all deactivated Constraint components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all deactivated Constraint components block
    """
    for c in activated_block_component_generator(block, ctype=Constraint):
        if not c.active:
            yield c


def deactivated_constraints_set(block):
    """
    Method to return a ComponentSet of all deactivated Constraint components in
    a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all deactivated Constraint components in block
    """
    return ComponentSet(deactivated_constraints_generator(block))


def number_deactivated_constraints(block):
    """
    Method to return the number of deactivated Constraint components in a
    model. This will include number of deactivated equalities in a Greybox models
    using number_deactivated_greybox_equalities function.

    Args:
        block : model to be studied

    Returns:
        Number of deactivated Constraint components in block
    """
    standard_equalities = sum(1 for _ in deactivated_constraints_generator(block))
    greybox_equalities = number_deactivated_greybox_equalities(block)
    return standard_equalities + greybox_equalities


# -------------------------------------------------------------------------
# Equality Constraints
def total_equalities_generator(block):
    """
    Generator which returns all equality Constraint components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all equality Constraint components block
    """
    for c in activated_block_component_generator(block, ctype=Constraint):
        if c.upper is not None and c.lower is not None and c.upper == c.lower:
            yield c


def total_equalities_set(block):
    """
    Method to return a ComponentSet of all equality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all equality Constraint components in block
    """
    return ComponentSet(total_equalities_generator(block))


def number_total_equalities(block):
    """
    Method to return the total number of equality Constraint components in a
    model. This will include the number of activated equalities Greybox using the number_activated_greybox_equalities function.

    Args:
        block : model to be studied

    Returns:
        Number of equality Constraint components in block
    """
    standard_equalities = sum(1 for _ in total_equalities_generator(block))
    greybox_equalities = number_activated_greybox_equalities(block)
    return standard_equalities + greybox_equalities


def activated_equalities_generator(block):
    """
    Generator which returns all activated equality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all activated equality Constraint components
        block
    """
    for c in _iter_indexed_block_data_objects(
        block, Constraint, active=True, descend_into=True
    ):
        if (
            c.upper is not None
            and c.lower is not None
            and value(c.upper) == value(c.lower)
        ):
            yield c


def activated_equalities_set(block):
    """
    Method to return a ComponentSet of all activated equality Constraint
    components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all activated equality Constraint components
        in block
    """
    return ComponentSet(activated_equalities_generator(block))


def number_activated_equalities(block):
    """
    Method to return the number of activated equality Constraint components in
    a model. This will include number of equalities in Greybox model using number_activated_greybox_equalities function.

    Args:
        block : model to be studied

    Returns:
        Number of activated equality Constraint components in block
    """
    return sum(
        1 for _ in activated_equalities_generator(block)
    ) + number_activated_greybox_equalities(block)


def number_activated_greybox_equalities(block) -> int:
    """
    Function to compute total number of equality constraints for all GreyBox objects in this block.

    A GreyBox model is always assumed to be 0DOFs where each output[i]==f(inputs)
    where f is GreyBox model, this should be true regardless if
    GreyBox model is doing internal optimization or not, as every output
    is calculated through the GreyBox internal model using provided inputs.

    Args:
        block : pyomo concrete model or pyomo block

    Returns:
        Number of equality constraints in all GreyBox objects on the provided block
    """
    equalities = 0
    for grey_box in activated_greybox_block_set(block):
        equalities += len(grey_box.outputs)
        equalities += grey_box.get_external_model().n_equality_constraints()
    return equalities


def number_deactivated_greybox_equalities(block) -> int:
    """
    Function to compute total number of equality constraints for all GreyBox objects in this block.

    A GreyBox model is always assumed to be 0DOFs where each output[i]==f(inputs)
    where f is GreyBox model, this should be true regardless if
    GreyBox model is doing internal optimization or not, as every output
    is calculated through a the GreyBox internal model using provided inputs.

    Args:
        block : pyomo concrete model or pyomo block

    Returns:
        Number of equality constraints in all GreyBox objects on the provided block
    """
    equalities = 0
    for grey_box in deactivated_greybox_block_set(block):
        equalities += len(grey_box.outputs)
        equalities += grey_box.get_external_model().n_equality_constraints()
    return equalities


def deactivated_equalities_generator(block):
    """
    Generator which returns all deactivated equality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all deactivated equality Constraint
        components block
    """
    for c in total_equalities_generator(block):
        if not c.active:
            yield c


def deactivated_equalities_set(block):
    """
    Method to return a ComponentSet of all deactivated equality Constraint
    components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all deactivated equality Constraint components
        in block
    """
    return ComponentSet(deactivated_equalities_generator(block))


def number_deactivated_equalities(block):
    """
    Method to return the number of deactivated equality Constraint components
    in a model. This will include the number of deactivated equality constraints in Greybox models.

    Args:
        block : model to be studied

    Returns:
        Number of deactivated equality Constraint components in block
    """
    standard_equalities = sum(1 for _ in deactivated_equalities_generator(block))
    greybox_equalities = number_deactivated_greybox_equalities(block)
    return standard_equalities + greybox_equalities


# -------------------------------------------------------------------------
# Inequality Constraints
def total_inequalities_generator(block):
    """
    Generator which returns all inequality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all inequality Constraint components block
    """
    for c in activated_block_component_generator(block, ctype=Constraint):
        if c.upper is None or c.lower is None:
            yield c


def total_inequalities_set(block):
    """
    Method to return a ComponentSet of all inequality Constraint components in
    a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all inequality Constraint components in block
    """
    return ComponentSet(total_inequalities_generator(block))


def number_total_inequalities(block):
    """
    Method to return the total number of inequality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        Number of inequality Constraint components in block
    """
    return sum(1 for _ in total_inequalities_generator(block))


def activated_inequalities_generator(block):
    """
    Generator which returns all activated inequality Constraint components in a
    model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all activated inequality Constraint
        components block
    """
    for c in _iter_indexed_block_data_objects(
        block, Constraint, active=True, descend_into=True
    ):
        if c.upper is None or c.lower is None:
            yield c


def activated_inequalities_set(block):
    """
    Method to return a ComponentSet of all activated inequality Constraint
    components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all activated inequality Constraint components
        in block
    """
    return ComponentSet(activated_inequalities_generator(block))


def number_activated_inequalities(block):
    """
    Method to return the number of activated inequality Constraint components
    in a model.

    Args:
        block : model to be studied

    Returns:
        Number of activated inequality Constraint components in block
    """
    return sum(1 for _ in activated_inequalities_generator(block))


def deactivated_inequalities_generator(block):
    """
    Generator which returns all deactivated inequality Constraint components in
    a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all deactivated equality Constraint
        components block
    """
    for c in total_inequalities_generator(block):
        if not c.active:
            yield c


def deactivated_inequalities_set(block):
    """
    Method to return a ComponentSet of all deactivated inequality Constraint
    components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all deactivated inequality Constraint
        components in block
    """
    return ComponentSet(deactivated_inequalities_generator(block))


def number_deactivated_inequalities(block):
    """
    Method to return the number of deactivated inequality Constraint components
    in a model.

    Args:
        block : model to be studied

    Returns:
        Number of deactivated inequality Constraint components in block
    """
    return sum(1 for _ in deactivated_inequalities_generator(block))


# -------------------------------------------------------------------------
# Basic Variable Methods
# Always use ComponentSets for Vars to avoid duplication of References
# i.e. number methods should always use the ComponentSet, not a generator
def variables_set(block):
    """
    Method to return a ComponentSet of all Var components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components in block
    """
    var_set = ComponentSet()
    for var in _iter_indexed_block_data_objects(
        block, ctype=Var, active=True, descend_into=True
    ):
        var_set.add(var)
    for var in greybox_variables(block):
        var_set.add(var)
    return var_set


def number_variables(block):
    """
    Method to return the number of Var components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components in block
    """
    return len(variables_set(block))


def fixed_variables_generator(block):
    """
    Generator which returns all fixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all fixed Var components block
    """
    for v in _iter_indexed_block_data_objects(
        block, ctype=Var, active=True, descend_into=True
    ):
        if v.fixed:
            yield v
    # include greybox variables in set
    for v in greybox_variables(block):
        if v.fixed:
            yield v


def fixed_variables_set(block):
    """
    Method to return a ComponentSet of all fixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all fixed Var components in block
    """
    return ComponentSet(fixed_variables_generator(block))


def number_fixed_variables(block):
    """
    Method to return the number of fixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of fixed Var components in block
    """
    return len(fixed_variables_set(block))


def unfixed_variables_generator(block):
    """
    Generator which returns all unfixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all unfixed Var components block
    """
    for v in _iter_indexed_block_data_objects(
        block, ctype=Var, active=True, descend_into=True
    ):
        if not v.fixed:
            yield v


def unfixed_variables_set(block):
    """
    Method to return a ComponentSet of all unfixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all unfixed Var components in block
    """
    return ComponentSet(unfixed_variables_generator(block))


def number_unfixed_variables(block):
    """
    Method to return the number of unfixed Var components in a model.

    Args:
        block : model to be studied

    Returns:
        Number of unfixed Var components in block
    """
    return len(unfixed_variables_set(block))


def variables_near_bounds_generator(
    block,
    tol=None,
    relative=None,
    skip_lb=False,
    skip_ub=False,
    abs_tol=1e-4,
    rel_tol=1e-4,
):
    """
    Generator which returns all Var components in a model which have a value
    within tol (default: relative) of a bound.

    Args:
        block : model to be studied
        abs_tol : absolute tolerance for inclusion in generator (default = 1e-4)
        rel_tol : relative tolerance for inclusion in generator (default = 1e-4)
        skip_lb: Boolean to skip lower bound (default = False)
        skip_ub: Boolean to skip upper bound (default = False)

    Returns:
        A generator which returns all Var components block that are close to a
        bound
    """
    # Check for deprecated arguments
    if relative is not None:
        msg = (
            "variables_near_bounds_generator has deprecated the relative argument. "
            "Please set abs_tol and rel_tol arguments instead."
        )
        deprecation_warning(msg=msg, logger=_log, version="2.2.0", remove_in="3.0.0")
    if tol is not None:
        msg = (
            "variables_near_bounds_generator has deprecated the tol argument. "
            "Please set abs_tol and rel_tol arguments instead."
        )
        deprecation_warning(msg=msg, logger=_log, version="2.2.0", remove_in="3.0.0")
        # Set tolerances using the provided value
        abs_tol = tol
        rel_tol = tol

    for v in _iter_indexed_block_data_objects(
        block, ctype=Var, active=True, descend_into=True
    ):
        # To avoid errors, check that v has a value
        if v.value is None:
            continue

        # First, magnitude of variable
        if v.ub is not None and v.lb is not None:
            # Both upper and lower bounds, apply tol to (upper - lower)
            mag = value(v.ub - v.lb)
        elif v.ub is not None:
            # Only upper bound, apply tol to bound value
            mag = abs(value(v.ub))
        elif v.lb is not None:
            # Only lower bound, apply tol to bound value
            mag = abs(value(v.lb))
        else:
            mag = 0

        # Calculate largest tolerance from absolute and relative
        tol = max(abs_tol, mag * rel_tol)

        if v.ub is not None and not skip_ub and value(v.ub - v.value) <= tol:
            yield v
        elif v.lb is not None and not skip_lb and value(v.value - v.lb) <= tol:
            yield v


def variables_near_bounds_set(
    block,
    tol=None,
    relative=None,
    skip_lb=False,
    skip_ub=False,
    abs_tol=1e-4,
    rel_tol=1e-4,
):
    """
    Method to return a ComponentSet of all Var components in a model which have
    a value within tolerance of a bound.

    Args:
        block : model to be studied
        abs_tol : absolute tolerance for inclusion in generator (default = 1e-4)
        rel_tol : relative tolerance for inclusion in generator (default = 1e-4)
        skip_lb: Boolean to skip lower bound (default = False)
        skip_ub: Boolean to skip upper bound (default = False)

    Returns:
        A ComponentSet including all Var components block that are close to a
        bound
    """
    return ComponentSet(
        variables_near_bounds_generator(
            block, tol, relative, skip_lb, skip_ub, abs_tol, rel_tol
        )
    )


def number_variables_near_bounds(block, tol=None, abs_tol=1e-4, rel_tol=1e-4):
    """
    Method to return the number of all Var components in a model which have
    a value within tol (relative) of a bound.

    Args:
        block : model to be studied
        abs_tol : absolute tolerance for inclusion in generator (default = 1e-4)
        rel_tol : relative tolerance for inclusion in generator (default = 1e-4)

    Returns:
        Number of components block that are close to a bound
    """
    return len(
        variables_near_bounds_set(block, tol=tol, abs_tol=abs_tol, rel_tol=rel_tol)
    )


# -------------------------------------------------------------------------
# Variables in Constraints
def variables_in_activated_constraints_set(block):
    """
    Method to return a ComponentSet of all Var components which appear within a
    Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which appear within
        activated Constraints in block
    """
    var_set = ComponentSet()
    for c in _iter_indexed_block_data_objects(
        block, ctype=Constraint, active=True, descend_into=True
    ):
        for v in identify_variables(c.body):
            var_set.add(v)
    # include any vars in greyboxes
    for v in greybox_variables(block):
        var_set.add(v)
    return var_set


def number_variables_in_activated_constraints(block):
    """
    Method to return the number of Var components that appear within active
    Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which appear within active Constraints in
        block
    """
    return len(variables_in_activated_constraints_set(block))


def variables_not_in_activated_constraints_set(block):
    """
    Method to return a ComponentSet of all Var components which do not appear within a
    Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which do not appear within
        activated Constraints in block
    """
    var_set = ComponentSet()

    active_vars = variables_in_activated_constraints_set(block)

    for v in _iter_indexed_block_data_objects(
        block, ctype=Var, active=True, descend_into=True
    ):
        if v not in active_vars:
            var_set.add(v)
    return var_set


def number_variables_not_in_activated_constraints(block):
    """
    Method to return the number of Var components that do not appear within active
    Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which do not appear within active Constraints in
        block
    """
    return len(variables_not_in_activated_constraints_set(block))


def variables_in_activated_equalities_set(block):
    """
    Method to return a ComponentSet of all Var components which appear within
    an equality Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which appear within
        activated equality Constraints in block
    """
    var_set = ComponentSet()
    for c in activated_equalities_generator(block):
        for v in identify_variables(c.body):
            var_set.add(v)
    # include any vars in greyboxes
    for v in greybox_variables(block):
        var_set.add(v)
    return var_set


def number_variables_in_activated_equalities(block):
    """
    Method to return the number of Var components which appear within activated
    equality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which appear within activated equality
        Constraints in block
    """
    return len(variables_in_activated_equalities_set(block))


def variables_in_activated_inequalities_set(block):
    """
    Method to return a ComponentSet of all Var components which appear within
    an inequality Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which appear within
        activated inequality Constraints in block
    """
    var_set = ComponentSet()
    for c in activated_inequalities_generator(block):
        for v in identify_variables(c.body):
            var_set.add(v)
    return var_set


def number_variables_in_activated_inequalities(block):
    """
    Method to return the number of Var components which appear within activated
    inequality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which appear within activated inequality
        Constraints in block
    """
    return len(variables_in_activated_inequalities_set(block))


def variables_only_in_inequalities(block):
    """
    Method to return a ComponentSet of all Var components which appear only
    within inequality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which appear only within
        inequality Constraints in block
    """
    return variables_in_activated_inequalities_set(
        block
    ) - variables_in_activated_equalities_set(block)


def number_variables_only_in_inequalities(block):
    """
    Method to return the number of Var components which appear only within
    activated inequality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which appear only within activated inequality
        Constraints in block
    """
    return len(variables_only_in_inequalities(block))


# -------------------------------------------------------------------------
# Fixed Variables in Constraints
def fixed_variables_in_activated_equalities_set(block):
    """
    Method to return a ComponentSet of all fixed Var components which appear
    within an equality Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all fixed Var components which appear within
        activated equality Constraints in block
    """
    var_set = ComponentSet()
    for v in variables_in_activated_equalities_set(block):
        if v.fixed:
            var_set.add(v)
    return var_set


def number_fixed_variables_in_activated_equalities(block):
    """
    Method to return the number of fixed Var components which appear within
    activated equality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of fixed Var components which appear within activated equality
        Constraints in block
    """
    return len(fixed_variables_in_activated_equalities_set(block))


def unfixed_variables_in_activated_equalities_set(block):
    """
    Method to return a ComponentSet of all unfixed Var components which appear
    within an activated equality Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet of all unfixed Var components which appear within
        activated equality Constraints in block
    """
    var_set = ComponentSet()
    for v in variables_in_activated_equalities_set(block):
        if not v.fixed:
            var_set.add(v)
    return var_set


def unfixed_greybox_variables(block):
    """
    Function to return a ComponentSet of all unfixed Var in GreyBoxModels

    Args:
        block : model to be studied

    Returns:
        A ComponentSet of all unfixed Var components which appear in Greybox models
    """
    var_set = ComponentSet()
    for var in greybox_variables(block):
        if not var.fixed:
            var_set.add(var)
    return var_set


def greybox_variables(block):
    """
    Function to return a ComponentSet of all Var in GreyBoxModels

    Args:
        block : model to be studied

    Returns:
        A ComponentSet of all Var components which appear within
        activated Greybox model blocks
    """
    var_set = ComponentSet()
    for grey_box in activated_greybox_block_set(block):
        for in_var in grey_box.inputs:
            var_set.add(grey_box.inputs[in_var])
        for out_var in grey_box.outputs:
            var_set.add(grey_box.outputs[out_var])
    return var_set


def number_of_unfixed_greybox_variables(block):
    """
    Function to return a number of unfixed variables in grey box
    Args:
        block : model to be studied

    Returns:
        number of unfixed greybox variables
    """

    return len(unfixed_greybox_variables(block))


def number_of_greybox_variables(block):
    """
    Function to return a number of variables in grey box
    Args:
        block : model to be studied

    Returns:
        number of greybox variables
    """

    return len(greybox_variables(block))


def number_unfixed_variables_in_activated_equalities(block):
    """
    Method to return the number of unfixed Var components which appear within
    activated equality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of unfixed Var components which appear within activated equality
        Constraints in block
    """
    return len(unfixed_variables_in_activated_equalities_set(block))


def fixed_variables_only_in_inequalities(block):
    """
    Method to return a ComponentSet of all fixed Var components which appear
    only within activated inequality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all fixed Var components which appear only
        within activated inequality Constraints in block
    """
    var_set = ComponentSet()
    for v in variables_only_in_inequalities(block):
        if v.fixed:
            var_set.add(v)
    return var_set


def number_fixed_variables_only_in_inequalities(block):
    """
    Method to return the number of fixed Var components which only appear
    within activated inequality Constraints in a model.

    Args:
        block : model to be studied

    Returns:
        Number of fixed Var components which only appear within activated
        inequality Constraints in block
    """
    return len(fixed_variables_only_in_inequalities(block))


# -------------------------------------------------------------------------
# Unused and un-Transformed Variables
def unused_variables_set(block):
    """
    Method to return a ComponentSet of all Var components which do not appear
    within any activated Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which do not appear within
        any Constraints in block
    """
    return variables_set(block) - variables_in_activated_constraints_set(block)


def number_unused_variables(block):
    """
    Method to return the number of Var components which do not appear within
    any activated Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which do not appear within any activated
        Constraints in block
    """
    return len(unused_variables_set(block))


def fixed_unused_variables_set(block):
    """
    Method to return a ComponentSet of all fixed Var components which do not
    appear within any activated Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all fixed Var components which do not appear
        within any Constraints in block
    """
    var_set = ComponentSet()
    for v in unused_variables_set(block):
        if v.fixed:
            var_set.add(v)
    return var_set


def number_fixed_unused_variables(block):
    """
    Method to return the number of fixed Var components which do not appear
    within any activated Constraint in a model.

    Args:
        block : model to be studied

    Returns:
        Number of fixed Var components which do not appear within any activated
        Constraints in block
    """
    return len(fixed_unused_variables_set(block))


def derivative_variables_set(block):
    """
    Method to return a ComponentSet of all DerivativeVar components which
    appear in a model. Users should note that DerivativeVars are converted to
    ordinary Vars when a DAE transformation is applied. Thus, this method is
    useful for detecting any DerivativeVars which were do transformed.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all DerivativeVar components which appear in
        block
    """
    return ComponentSet(
        _iter_indexed_block_data_objects(
            block, ctype=DerivativeVar, active=True, descend_into=True
        )
    )


def number_derivative_variables(block):
    """
    Method to return the number of DerivativeVar components which
    appear in a model. Users should note that DerivativeVars are converted to
    ordinary Vars when a DAE transformation is applied. Thus, this method is
    useful for detecting any DerivativeVars which were do transformed.

    Args:
        block : model to be studied

    Returns:
        Number of DerivativeVar components which appear in block
    """
    return len(derivative_variables_set(block))


# -------------------------------------------------------------------------
# Objective methods
def total_objectives_generator(block):
    """
    Generator which returns all Objective components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all Objective components block
    """
    for o in activated_block_component_generator(block, ctype=Objective):
        yield o


def total_objectives_set(block):
    """
    Method to return a ComponentSet of all Objective components which appear
    in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Objective components which appear in block
    """
    return ComponentSet(total_objectives_generator(block))


def number_total_objectives(block):
    """
    Method to return the number of Objective components which appear in a model

    Args:
        block : model to be studied

    Returns:
        Number of Objective components which appear in block
    """
    return sum(1 for _ in total_objectives_generator(block))


def activated_objectives_generator(block):
    """
    Generator which returns all activated Objective components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all activated Objective components block
    """
    for o in activated_block_component_generator(block, ctype=Objective):
        if o.active:
            yield o


def activated_objectives_set(block):
    """
    Method to return a ComponentSet of all activated Objective components which
    appear in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all activated Objective components which
        appear in block
    """
    return ComponentSet(activated_objectives_generator(block))


def number_activated_objectives(block):
    """
    Method to return the number of activated Objective components which appear
    in a model.

    Args:
        block : model to be studied

    Returns:
        Number of activated Objective components which appear in block
    """
    return sum(1 for _ in activated_objectives_generator(block))


def deactivated_objectives_generator(block):
    """
    Generator which returns all deactivated Objective components in a model.

    Args:
        block : model to be studied

    Returns:
        A generator which returns all deactivated Objective components block
    """
    for o in activated_block_component_generator(block, ctype=Objective):
        if not o.active:
            yield o


def deactivated_objectives_set(block):
    """
    Method to return a ComponentSet of all deactivated Objective components
    which appear in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all deactivated Objective components which
        appear in block
    """
    return ComponentSet(deactivated_objectives_generator(block))


def number_deactivated_objectives(block):
    """
    Method to return the number of deactivated Objective components which
    appear in a model.

    Args:
        block : model to be studied

    Returns:
        Number of deactivated Objective components which appear in block
    """
    return sum(1 for _ in deactivated_objectives_generator(block))


# -------------------------------------------------------------------------
# Expression methods
# Always use ComponentsSets here to avoid duplication of References
def expressions_set(block):
    """
    Method to return a ComponentSet of all Expression components which appear
    in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Expression components which  appear in
        block
    """
    return ComponentSet(
        _iter_indexed_block_data_objects(
            block, ctype=Expression, active=True, descend_into=True
        )
    )


def number_expressions(block):
    """
    Method to return the number of Expression components which appear in a
    model.

    Args:
        block : model to be studied

    Returns:
        Number of Expression components which  appear in block
    """
    return len(expressions_set(block))


# -------------------------------------------------------------------------
# Other model statistics
def degrees_of_freedom(block):
    """
    Method to return the degrees of freedom of a model.

    Args:
        block : model to be studied

    Returns:
        Number of degrees of freedom in block.
    """
    return number_unfixed_variables_in_activated_equalities(
        block
    ) - number_activated_equalities(block)


def large_residuals_set(block, tol=1e-5, return_residual_values=False):
    """
    Method to return a ComponentSet of all Constraint components with a
    residual greater than a given threshold which appear in a model.

    Args:
        block : model to be studied
        tol : residual threshold for inclusion in ComponentSet
        return_residual_values: boolean, if true return dictionary with
            residual values

    Returns:
        large_residual_set: A ComponentSet including all Constraint components
        with a residual greater than tol which appear in block (if
        return_residual_values is false) residual_values: dictionary with
        constraint as key and residual (float) as value (if
        return_residual_values is true)
    """
    large_residuals_set = ComponentSet()
    if return_residual_values:
        residual_values = dict()
    for c in _iter_indexed_block_data_objects(
        block, ctype=Constraint, active=True, descend_into=True
    ):
        try:
            r = 0.0  # residual

            # skip if no lower bound set
            if c.lower is None:
                r_temp = 0
            else:
                r_temp = value(c.lower - c.body())
            # update the residual
            if r_temp > r:
                r = r_temp

            # skip if no upper bound set
            if c.upper is None:
                r_temp = 0
            else:
                r_temp = value(c.body() - c.upper)

            # update the residual
            if r_temp > r:
                r = r_temp

            # save residual if it is above threshold
            if r > tol:
                large_residuals_set.add(c)

                if return_residual_values:
                    residual_values[c] = r
        except (AttributeError, TypeError, ValueError):
            large_residuals_set.add(c)

            if return_residual_values:
                residual_values[c] = None

    if return_residual_values:
        return residual_values
    else:
        return large_residuals_set


def number_large_residuals(block, tol=1e-5):
    """
    Method to return the number Constraint components with a residual greater
    than a given threshold which appear in a model.

    Args:
        block : model to be studied
        tol : residual threshold for inclusion in ComponentSet

    Returns:
        Number of Constraint components with a residual greater than tol which
        appear in block
    """
    lr = 0
    for c in _iter_indexed_block_data_objects(
        block, ctype=Constraint, active=True, descend_into=True
    ):
        if c.active and value(c.lower - c.body()) > tol:
            lr += 1
        elif c.active and value(c.body() - c.upper) > tol:
            lr += 1
    return lr


def active_variables_in_deactivated_blocks_set(block):
    """
    Method to return a ComponentSet of any Var components which appear within
    an active Constraint but belong to a deactivated Block in a model.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including any Var components which belong to a
        deactivated Block but appear in an activate Constraint in block
    """
    var_set = ComponentSet()
    block_set = activated_blocks_set(block)
    for v in variables_in_activated_constraints_set(block):
        if v.parent_block() not in block_set:
            var_set.add(v)
    return var_set


def number_active_variables_in_deactivated_blocks(block):
    """
    Method to return the number of Var components which appear within an active
    Constraint but belong to a deactivated Block in a model.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which belong to a deactivated Block but appear
        in an activate Constraint in block
    """
    return len(active_variables_in_deactivated_blocks_set(block))


def variables_with_none_value_in_activated_equalities_set(block):
    """
    Method to return a ComponentSet of all Var components which
    have a value of None in the set of activated constraints.

    Args:
        block : model to be studied

    Returns:
        A ComponentSet including all Var components which
        have a value of None in the set of activated constraints.
    """
    var_set = ComponentSet()
    for v in variables_in_activated_equalities_set(block):
        if v.value is None:
            var_set.add(v)
    return var_set


def number_variables_with_none_value_in_activated_equalities(block):
    """
    Method to return the number of Var components which
    have a value of None in the set of activated constraints.

    Args:
        block : model to be studied

    Returns:
        Number of Var components which
        have a value of None in the set of activated constraints.
    """

    return len(variables_with_none_value_in_activated_equalities_set(block))


# -------------------------------------------------------------------------
# Reporting methods
def report_statistics(block, ostream=None):
    """
    Method to print a report of the model statistics for a Pyomo Block

    Args:
        block : the Block object to report statistics from
        ostream : output stream for printing (defaults to sys.stdout)

    Returns:
        Printed output of the model statistics
    """
    if ostream is None:
        ostream = sys.stdout

    tab = " " * 4
    header = "=" * 72

    if block.name == "unknown":
        name_str = ""
    else:
        name_str = f"-  {block.name}"

    ostream.write("\n")
    ostream.write(header + "\n")
    ostream.write(f"Model Statistics  {name_str} \n")
    ostream.write("\n")
    ostream.write(f"Degrees of Freedom: " f"{degrees_of_freedom(block)} \n")
    ostream.write("\n")
    ostream.write(f"Total No. Variables: " f"{number_variables(block)} \n")
    ostream.write(
        f"{tab}No. Fixed Variables: " f"{number_fixed_variables(block)}" f"\n"
    )
    ostream.write(
        f"{tab}No. Unused Variables: "
        f"{number_unused_variables(block)} (Fixed):"
        f"{number_fixed_unused_variables(block)})"
        f"\n"
    )
    nv_alias = number_variables_only_in_inequalities
    nfv_alias = number_fixed_variables_only_in_inequalities
    ostream.write(
        f"{tab}No. Variables only in Inequalities:"
        f" {nv_alias(block)}"
        f" (Fixed: {nfv_alias(block)}) \n"
    )
    ostream.write("\n")
    ostream.write(f"Total No. Constraints: " f"{number_total_constraints(block)} \n")
    ostream.write(
        f"{tab}No. Equality Constraints: "
        f"{number_total_equalities(block)}"
        f" (Deactivated: "
        f"{number_deactivated_equalities(block)})"
        f"\n"
    )
    ostream.write(
        f"{tab}No. Inequality Constraints: "
        f"{number_total_inequalities(block)}"
        f" (Deactivated: "
        f"{number_deactivated_inequalities(block)})"
        f"\n"
    )
    ostream.write("\n")
    ostream.write(
        f"No. Objectives: "
        f"{number_total_objectives(block)}"
        f" (Deactivated: "
        f"{number_deactivated_objectives(block)})"
        f"\n"
    )
    ostream.write("\n")
    ostream.write(
        f"No. Blocks: {number_total_blocks(block)}"
        f" (Deactivated: "
        f"{number_deactivated_blocks(block)}) \n"
    )
    ostream.write(f"No. Expressions: " f"{number_expressions(block)} \n")
    if number_activated_greybox_blocks(block) != 0:
        ostream.write(
            f"No. Activated GreyBox Blocks: {number_activated_greybox_blocks(block)} \n"
        )
        ostream.write(f"No. GreyBox Variables: {number_of_greybox_variables(block)} \n")
        ostream.write(
            f"No. Fixed GreyBox Variables: {number_of_greybox_variables(block)-number_of_unfixed_greybox_variables(block)} \n"
        )
        ostream.write(
            f"No. GreyBox Equalities: {number_activated_greybox_equalities(block)} \n"
        )
    ostream.write(header + "\n")
    ostream.write("\n")


# -------------------------------------------------------------------------
# Common sub-methods
def activated_block_component_generator(block, ctype):
    """
    Generator which returns all the components of a given ctype which exist in
    activated Blocks within a model.

    Args:
        block : model to be studied
        ctype : type of Pyomo component to be returned by generator.

    Returns:
        A generator which returns all components of ctype which appear in
        activated Blocks in block
    """
    # Yield local components first
    for c in _iter_indexed_block_data_objects(
        block, ctype=ctype, active=None, descend_into=False
    ):
        yield c

    # Then yield components in active sub-blocks
    for b in _iter_indexed_block_data_objects(
        block, ctype=Block, active=True, descend_into=True
    ):
        for c in b.component_data_objects(ctype=ctype, active=None, descend_into=False):
            yield c
