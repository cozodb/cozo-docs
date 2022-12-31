==============
Aggregations
==============


Aggregations in Cozo can be thought of as a function that acts on a stream of values
and produces a single value (the aggregate).

There are two kinds of aggregations in Cozo, *ordinary aggregations* and *semi-lattice aggregations*.
They are implemented differently in Cozo, with semi-lattice aggregations more powerful
(only the latter can be used recursively).

The power of semi-lattice aggregations derive from the additional properties they satisfy: a `semilattice <https://en.wikipedia.org/wiki/Semilattice>`_:

    idempotency
        the aggregate of a single value ``a`` is ``a`` itself,
    commutativity
        the aggregate of ``a`` then ``b`` is equal to the aggregate of ``b`` then ``a``,
    associativity
        it is immaterial where we put the parentheses in an aggregate application.

In auto-recursive semi-lattice aggregations, there are soundness constraints on what can be done on the bindings coming from the auto-recursive parts 
within the body of the rule. Usually you do not need to worry about this at all since the obvious ways of using this functionality are all sound,
but as for non-termination due to fresh variables introduced by function applications,
Cozo does not (and cannot) check for unsoundness in this case.

------------------------------------
Semi-lattice aggregations
------------------------------------

.. module:: Aggr.SemiLattice
    :noindex:

.. function:: min(x)

    Aggregate the minimum value of all ``x``.

.. function:: max(x)

    Aggregate the maximum value of all ``x``.

.. function:: and(var)

    Aggregate the logical conjunction of the variable passed in.

.. function:: or(var)

    Aggregate the logical disjunction of the variable passed in.

.. function:: union(var)

    Aggregate the unions of ``var``, which must be a list.

.. function:: intersection(var)

    Aggregate the intersections of ``var``, which must be a list.

.. function:: choice(var)

    Returns a non-null value. If all values are null, returns ``null``. Which one is returned is deterministic but implementation-dependent
    and may change from version to version.

.. function:: min_cost([data, cost])

    The argument should be a list of two elements and this aggregation chooses the list of the minimum ``cost``.

.. function:: shortest(var)

    ``var`` must be a list. Returns the shortest list among all values. Ties will be broken non-deterministically.

.. function:: bit_and(var)

    ``var`` must be bytes. Returns the bitwise 'and' of the values.

.. function:: bit_or(var)

    ``var`` must be bytes. Returns the bitwise 'or' of the values.

---------------------
Ordinary aggregations
---------------------

.. module:: Aggr.Ord
    :noindex:

.. function:: count(var)

    Count how many values are generated for ``var`` (using bag instead of set semantics).

.. function:: count_unique(var)

    Count how many unique values there are for ``var``.

.. function:: collect(var)

    Collect all values for ``var`` into a list.

.. function:: unique(var)

    Collect ``var`` into a list, keeping each unique value only once.

.. function:: group_count(var)

    Count the occurrence of unique values of ``var``, putting the result into a list of lists,
    e.g. when applied to ``'a'``, ``'b'``, ``'c'``, ``'c'``, ``'a'``, ``'c'``, the results is ``[['a', 2], ['b', 1], ['c', 3]]``.

.. function:: bit_xor(var)

    ``var`` must be bytes. Returns the bitwise 'xor' of the values.

.. function:: latest_by([data, time])

    The argument should be a list of two elements and this aggregation returns the ``data`` of the maximum ``time``.
    This is very similar to ``min_cost``, the differences being that maximum instead of minimum is used,
    and non-numerical costs are allowed.
    Only ``data`` is returned. 

.. function:: smallest_by([data, cost])

    The argument should be a list of two elements and this aggregation returns the ``data`` of the minimum ``cost``.
    Non-numerical costs are allowed, unlike ``min_cost``. The value ``null`` for ``cost`` are ignored when comparing.

.. function:: choice_rand(var)

    Non-deterministically chooses one of the values of ``var`` as the aggregate.
    Each value the aggregation encounters has the same probability of being chosen.

    .. NOTE::
        This version of ``choice`` is not a semi-lattice aggregation
        since it is impossible to satisfy the uniform sampling requirement while maintaining no state,
        which is an implementation restriction unlikely to be lifted.

^^^^^^^^^^^^^^^^^^^^^^^^^
Statistical aggregations
^^^^^^^^^^^^^^^^^^^^^^^^^

.. function:: mean(x)

    The mean value of ``x``.

.. function:: sum(x)

    The sum of ``x``.

.. function:: product(x)

    The product of ``x``.

.. function:: variance(x)

    The sample variance of ``x``.

.. function:: std_dev(x)

    The sample standard deviation of ``x``.
