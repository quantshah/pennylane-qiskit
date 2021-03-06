# Copyright 2019 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
IBMQ Device
===========

**Module name:** :mod:`pennylane_qiskit.ibmq`

.. currentmodule:: pennylane_qiskit.ibmq

This module contains the :class:`~.IBMQDevice` class, a PennyLane device that allows
evaluation and differentiation of IBM Q's Quantum Processing Units (QPUs)
using PennyLane.

Classes
-------

.. autosummary::
   IBMQDevice

Code details
~~~~~~~~~~~~
"""
import os
import warnings

from qiskit import IBMQ
from qiskit.providers.ibmq.exceptions import IBMQAccountError

from .qiskit_device import QiskitDevice


class IBMQDevice(QiskitDevice):
    """A PennyLane device for the IBMQ API (remote) backend.

    For more details, see the `Qiskit documentation <https://qiskit.org/documentation/autodoc/qiskit.providers.ibmq.html>`_.

    You need to register at `IBMQ <https://quantum-computing.ibm.com/>`_ in order to
    recieve a token that is used for authentication using the API.

    As of the writing of this documentation, the API is free of charge, although
    there is a credit system to limit access to the quantum devices.

    Args:
        wires (int): The number of qubits of the device
        provider (Provider): The IBM Q provider you wish to use. If not provided,
            then the default provider returned by ``IBMQ.get_provider()`` is used.
        backend (str): the desired provider backend
        shots (int): number of circuit evaluations/random samples used
            to estimate expectation values and variances of observables

    Keyword Args:
        ibmqx_token (str): The IBM Q API token. If not provided, the environment
            variable ``IBMQX_TOKEN`` is used.
        ibmqx_url (str): The IBM Q URL. If not provided, the environment
            variable ``IBMQX_URL`` is used, followed by the default URL.
    """

    short_name = "qiskit.ibmq"
    _backend_kwargs = ["verbose", "backend", "ibmqx_token", "ibmqx_url"]

    def __init__(self, wires, provider=None, backend="ibmq_qasm_simulator", shots=1024, **kwargs):
        token = os.getenv("IBMQX_TOKEN") or kwargs.get("ibmqx_token", None)
        url = os.getenv("IBMQX_URL") or kwargs.get("ibmqx_url", None)

        if token is not None:
            # token was provided by the user, so attempt to enable an
            # IBM Q account manually
            ibmq_kwargs = {"url": url} if url is not None else {}
            IBMQ.enable_account(token, **ibmq_kwargs)
        else:
            # turn off deprecation warnings
            # TODO: remove IBM Q v1 API calls when fully deprecated
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)

                # check if an IBM Q account is already active.
                #
                # * IBMQ v1 credentials stored in active_accounts().
                #   If no accounts are active, it returns []
                #
                # * IBMQ v2 credentials stored in active_account().
                #   If no accounts are active, it returns None.

                if IBMQ.active_account() is None and not IBMQ.active_accounts():
                    # no active account
                    try:
                        # attempt to load a v1 account stored on disk
                        IBMQ.load_accounts()
                    except IBMQAccountError:
                        try:
                            # attempt to load a v2 account stored on disk
                            IBMQ.load_account()
                        except IBMQAccountError:
                            # attempt to enable an account manually using
                            # a provided token
                            raise IBMQAccountError(
                                "No active IBM Q account, and no IBM Q token provided."
                            ) from None

        # IBM Q account is now enabled

        # get a provider
        p = provider or IBMQ.get_provider()

        super().__init__(wires=wires, provider=p, backend=backend, shots=shots, **kwargs)
