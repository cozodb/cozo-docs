=======================================
Tips for writing queries
=======================================

------------------------------
Dealing with nulls
------------------------------

Cozo is strict about types. A simple query such as::

    ?[a] := *rel[a, b], b > 0

will throw if some of the ``b`` are null: comparisons can only be made between values of the same type.
There are various ways you can deal with it: if you decide that the condition should be ``false`` if values are
not of the same type, you write::

    ?[a] := *rel[a, b], try(b > 0, false)

Alternatively, you may decide to consider any ``null`` values to be equivalent to some default values, 
in which case you write::

    ?[a] := *rel[a, b], (b ~ -1) > 0

here ``~`` is the ``coalesce`` operator. The parentheses are actually not necessary, but it reads better this way.
We recommend using the ``coalesce`` operator over using ``try``, since it is more explicit.

You can also be very explicit::

    ?[a] := *rel[a, b], if(is_null(b), false, b > 0)

but this is rather verbose. ``cond`` is also helpful in this case.

------------------------------
How to join
------------------------------