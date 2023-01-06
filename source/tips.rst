=======================================
Tips for writing queries
=======================================

------------------------------
Dealing with nulls
------------------------------

Cozo is strict about types. A simple query such as::

    ?[a] := *rel[a, b], b > 0

will throw if some of the ``b`` is null: comparisons can only be made between values of the same type.
There are various ways you can deal with it: if you decide that the condition should be ``false`` if values are
not of the same type, you write::

    ?[a] := *rel[a, b], try(b > 0, false)

Alternatively, you may decide to consider any ``null`` values to be equivalent to some default values, 
in which case you write::

    ?[a] := *rel[a, b], (b ~ -1) > 0

here ``~`` is the ``coalesce`` operator. The parentheses are not necessary, but it reads better this way.
We recommend using the ``coalesce`` operator over using ``try``, since it is more explicit.

You can also be very explicit::

    ?[a] := *rel[a, b], if(is_null(b), false, b > 0)

but this is rather verbose. ``cond`` is also helpful in this case.

------------------------------
How to join relations
------------------------------

Suppose we have the following relation::

    :create friend {fr, to}

Let's say we want to find Alice's friends' friends' friends' friends' friends. One way to write this is::

    ?[who] := *friends{fr: 'Alice', to: f1},
              *friends{fr: f1, to: f2},
              *friends{fr: f2, to: f3},
              *friends{fr: f3, to: f4},
              *friends{fr: f4, to: who}

Another way is::

    f1[who] := *friends{fr: 'Alice', to: who}
    f2[who] := f1[fr], *friends{fr, to: who}
    f3[who] := f2[fr], *friends{fr, to: who}
    f4[who] := f3[fr], *friends{fr, to: who}
    ?[who] := f4[fr], *friends{fr, to: who}

These two queries yield identical values. But on real networks, where loops abound, 
the second way of writing executes exponentially faster than the first.
Why? Because of set semantics in relations, the second way of writing deduplicates at every turn,
whereas the first way of writing builds up all paths to the final layer of friends.
In fact, even if there are no duplicates, the second version may still be faster, because in Cozo
rules run in parallel whenever allowed by semantics and available resources.

The moral of the story is, always prefer to break your query into smaller rules.
It usually reads better, and unlike in some other databases, 
it almost always executes faster in Cozo as well. But for this particular case, in which the query
is largely recursive, prefer to make it a recursive relation::

    f_n[who, min(layer)] := *friends{fr: 'Alice', to: who}, layer = 1
    f_n[who, min(layer)] := f_n[fr, last_layer], *friends{fr, to: who}, layer = last_layer + 1, layer <= 5
    ?[who] := f_n[who, 5]

The condition ``layer <= 5`` is necessary to ensure termination.

Are there any situations where the first way of writing is acceptable? Yes::

    ?[who] := *friends{fr: 'Alice', to: f1},
              *friends{fr: f1, to: f2},
              *friends{fr: f2, to: f3},
              *friends{fr: f3, to: f4},
              *friends{fr: f4, to: who}
    :limit 1

in this case, we stop at the first path, and this way of writing avoids the overhead of multiple rules
and is perhaps very slightly faster.

Also, if you want to count the different paths, you must write::

    ?[count(who)] := *friends{fr: 'Alice', to: f1},
                     *friends{fr: f1, to: f2},
                     *friends{fr: f2, to: f3},
                     *friends{fr: f3, to: f4},
                     *friends{fr: f4, to: who}

The multiple-rules way of writing gives wrong results due to set semantics.
Due to the presence of the aggregation ``count``, this query only keeps a single path in memory at any instant,
so it won't blow up your memory even on web-scale data.