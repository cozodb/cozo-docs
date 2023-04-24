====================================
Stored relations and transactions
====================================

In Cozo, data are stored in *stored relations* on disk.

---------------------------
Stored relations
---------------------------

To query stored relations,
use the ``*relation[...]`` or ``*relation{...}`` atoms in inline or fixed rules,
as explained in the :doc:`last chapter <queries>`.
To manipulate stored relations, use one of the following query options:

.. module:: QueryOp
    :noindex:

.. function:: :create <NAME> <SPEC>

    Create a stored relation with the given name and spec.
    No stored relation with the same name can exist beforehand.
    If a query is specified, data from the resulting relation is put into the newly created stored relation.
    This is the only stored relation-related query option in which a query may be omitted.

.. function:: :replace <NAME> <SPEC>

    Similar to ``:create``, except that if the named stored relation exists beforehand,
    it is completely replaced. The schema of the replaced relation need not match the new one.
    You cannot omit the query for ``:replace``.
    If there are any triggers associated, they will be preserved. Note that this may lead to errors if ``:replace``
    leads to schema change.

.. function:: :put <NAME> <SPEC>

    Put rows from the resulting relation into the named stored relation.
    If keys from the data exist beforehand, the corresponding rows are replaced with new ones.

.. function:: :rm <NAME> <SPEC>

    Remove rows from the named stored relation. Only keys should be specified in ``<SPEC>``.
    Removing a non-existent key is not an error and does nothing.

.. function:: :ensure <NAME> <SPEC>

    Ensure that rows specified by the output relation and spec exist in the database,
    and that no other process has written to these rows when the enclosing transaction commits.
    Useful for ensuring read-write consistency.

.. function:: :ensure_not <NAME> <SPEC>

    Ensure that rows specified by the output relation and spec do not exist in the database
    and that no other process has written to these rows when the enclosing transaction commits.
    Useful for ensuring read-write consistency.

You can rename and remove stored relations with the system ops ``::rename`` and ``::remove``,
described in the system op chapter.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Create and replace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The format of ``<SPEC>`` is identical for all ops, but the semantics is a bit different.
We first describe the format and semantics for ``:create`` and ``:replace``.

A spec, or a specification for columns, is enclosed in curly braces ``{}`` and separated by commas::

    ?[address, company_name, department_name, head_count] <- $input_data

    :create dept_info {
        company_name: String,
        department_name: String,
        =>
        head_count: Int,
        address: String,
    }

Columns before the symbol ``=>`` form the *keys* (actually a composite key) for the stored relation,
and those after it form the *values*.
If all columns are keys, the symbol ``=>`` may be omitted.
The order of columns matters.
Rows are stored in lexicographically sorted order in trees according to their keys.

In the above example, we explicitly specified the types for all columns.
In case of type mismatch,
the system will first try to coerce the values given, and if that fails, the query is aborted with an error.
You can omit types for columns, in which case their types default to ``Any?``,
i.e. all values are acceptable.
For example, the above query with all types omitted is::

    ?[address, company_name, department_name, head_count] <- $input_data

    :create dept_info { company_name, department_name => head_count, address }

In the example, the bindings for the output match the columns exactly (though not in the same order).
You can also explicitly specify the correspondence::

    ?[a, b, count(c)] <- $input_data

    :create dept_info {
        company_name = a,
        department_name = b,
        =>
        head_count = count(c),
        address: String = b
    }

You *must* use explicit correspondence if the entry head contains aggregation,
since names such as ``count(c)`` are not valid column names.
The ``address`` field above shows how to specify both a type and a correspondence.

Instead of specifying bindings, you can specify an expression that generates default values by using ``default``::

    ?[a, b] <- $input_data

    :create dept_info {
        company_name = a,
        department_name = b,
        =>
        head_count default 0,
        address default ''
    }

The expression is evaluated anew for each row, so if you specified a UUID-generating functions,
you will get a different UUID for each row.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Put, remove, ensure and ensure-not
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For ``:put``, ``:remove``, ``:ensure`` and ``:ensure_not``,
you do not need to specify all existing columns in the spec if the omitted columns have a default generator,
or if the type of the column is nullable, in which case the value defaults to ``null``.
For these operations, specifying default values does not have any effect and will not replace existing ones.

For ``:put`` and ``:ensure``, the spec needs to contain enough bindings to generate all keys and values.
For ``:rm`` and ``:ensure_not``, it only needs to generate all keys.

------------------------------------------------------
Chaining queries
------------------------------------------------------

Each script you send to Cozo is executed in its own transaction.
To ensure consistency of multiple operations on data,
You can define multiple queries in a single script,
by wrapping each query in curly braces ``{}``.
Each query can have its independent query options.
Execution proceeds for each query serially, and aborts at the first error encountered.
The returned relation is that of the last query.

The ``:assert (some|none)``, ``:ensure`` and ``:ensure_not`` query options allow you to express complicated constraints
that must be satisfied for your transaction to commit.

This example uses three queries to put and remove rows atomically
(either all succeed or all fail), and ensure that at the end of the transaction
an untouched row exists::

    {
        ?[a, b] <- [[1, 'one'], [3, 'three']]
        :put rel {a => b}
    }
    {
        ?[a] <- [[2]]
        :rm rel {a}
    }
    {
        ?[a, b] <- [[4, 'four']]
        :ensure rel {a => b}
    }

When a transaction starts, a snapshot is used,
so that only already committed data,
or data written within the same transaction, are visible to queries.
At the end of the transaction, changes are only committed if there are no conflicts
and no errors are raised.
If any mutation activate triggers, those triggers execute in the same transaction.

There is actually a mini-language hidden behind query chains. What you have seen above consists of a number of simple
*query expressions*, each expression is a complete query enclosed in braces, 
and the return value is the value of the last expression. There are other constructs as well:

* ``%if <cond> %then ... (%else ...) %end`` for conditional execution. 
  There is also a negated form beginning with ``%if_not``. The ``<cond>`` part is either a query expression or
  an ephemeral relation. Either way, the condition ends up being a relation, and a relation is considered truthy
  if the last field of its first row is truthy as determined by the ``to_bool`` function,
  and is considered falsy if the relation contains no rows, or the last field of its first row is falsy 
  as determined by the ``to_bool`` function.

* ``%loop ... %end`` for looping, you can use ``%break`` and ``%continue`` inside the loop. 
  You can prefix the loop with ``%mark <marker>``, and use ``%break <marker>`` or ``%continue marker`` 
  to jump sereral levels.

* ``%return <query expression or ephemeral relation, or empty>`` for early termination.

* ``%debug <ephemeral relation>`` for printing ephemeral relations to standard output.

* ``%ignore_error <query expression>`` executes the query expresison, but eats any error raised and continue.

* ``%swap <ephemeral relation> <another ephemeral relation>`` swaps two ephemeral relations.

What is the *ephemeral relation* mentioned above? This is a relation that can only be seen within the transaction
and which is gone when the transaction ends (hence it is useless in singleton queries). 
It is created and used in the same way as stored relations,
but with names starting with the underscore ``_``. You can think of them as variables in the chain query mini-language.

Let's see several examples::

    {:create _test {a}}

    %loop
        %if { len[count(x)] := *_test[x]; ?[x] := len[z], x = z >= 10 }
            %then %return _test
        %end
        { ?[a] := a = rand_uuid_v1(); :put _test {a} }
    %end

The return relation of this query consists of ten random rows. Note that in this example,
you *must not* use a constant rule when generating the random value: 
the body of a constant rule is evaluated to a constant only *once*, which will make the query loop forever.

Another one::

    {?[a] <- [[1], [2], [3]]; :replace _test {a}}

    %loop
        { ?[a] := *_test[a]; :limit 1; :rm _test {a} }
        %debug _test

        %if_not _test
        %then %break
        %end
    %end

    %return _test

The return relation of this query is empty (very contrived way of removing elements).

Finally::

    {?[a] <- [[1], [2], [3]]; :replace _test {a}}
    {?[a] <- []; :replace _test2 {a}}
    %swap _test _test2
    %return _test

The return relation of this query is empty as well, since the two ephemeral relations have been swapped.

We use this functionality to run ad-hoc iterative queries. As the basic query language is already Turing complete,
you can actually write any algorithm without this mini-language, but the way of writing may be very contrived.
Try implementing PageRank with basic query. You will end up with many recursive aggregations.
Next try with chained queries. A breeze.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Multi-statement transaction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Cozo also supports multi-statement in the hosting language for selected libraries (currently Rust, Python, NodeJS)
and the standalone executable. The way to use it is to request a transaction first,
do your queries and mutations against the transaction, and finally commit or abort the transaction.
This is more flexible than using the chaining query mini-language, but is specific to each hosting environment.
Please refer to the respective documentations of the environments.

-------------------------------------------------
Indices
-------------------------------------------------

Since version 0.5, it is possible to create indices on stored relations. 
In Cozo, indices are simply reordering of columns of the original stored relation.
As an example, let's say we have a relation 
::

    :create r {a => b}

but we often want to run queries like ``?[a] := *r{a, b: $value}``. Without indiecs, 
this will result in a full-scan. In this case we can do::

    ::index create r:idx {b, a}

You do *not* specify functional dependencies when creating indices (and in this case there are none anyway).

In Cozo, indices are read-only stored relations that you can query directly::

    ?[a] := *r:idx {a, b: $value}

In this case, running the original query will also use the index, 
and hence is equivalent to the explicit form (which you can confirm with ``::explain``).
However, Cozo is very conservative in using indices in that if there is any chance that the use of an index might
decrease performance, then Cozo will not use an index. Currently, this means that only in situations when 
using an index can avoid a full-scan will the index be used. 
This behaviour ensures that you will not need to fight against suboptimal use of indices with difficult tricks:
just be explicit.

To drop an index::

    ::index drop r:idx

In Cozo, you do not need to specify all columns when creating an index, 
and the database will complete the specified columns to a key. This means that if your stored relation is
::

    :create r {a, b => c, d, e}

and you created an index as::

    ::index create r:i {d, b}

the database will automatically run the following index creation instead::

    ::index create r:i {d, b, a}

You can see what columns are actually created by running ``::columns r:i``.

Indices can be used as inputs to fixed rules. They may also be eligible in time-travel queries, as long as
their last key column is of type ``Validity``.

------------------------------------------------------
Triggers
------------------------------------------------------

Cozo supports triggers attached to stored relations. 
You attach triggers to a stored relation by running the system op ``::set_triggers``::

    ::set_triggers <REL_NAME>

    on put { <QUERY> }
    on rm { <QUERY> }
    on replace { <QUERY> }
    on put { <QUERY> } # you can specify as many triggers as you need

``<QUERY>`` can be any valid query.

The ``on put`` triggers will run when new data is inserted or upserted,
which can be activated by ``:put``, ``:create`` and ``:replace`` query options.
The implicitly defined rules ``_new[]`` and ``_old[]`` can be used in the triggers, and
contain the added rows and the replaced rows respectively.

The ``on rm`` triggers will run when data is deleted, which can be activated by a ``:rm`` query option.
The implicitly defined rules ``_new[]`` and ``_old[]`` can be used in the triggers,
and contain the keys of the rows for deleted rows (even if no row with the key actually exist) and the rows
actually deleted (with both keys and non-keys).

The ``on replace`` triggers will be activated by a ``:replace`` query option.
They are run before any ``on put`` triggers.

All triggers for a relation must be specified together, in the same ``::set_triggers`` system op.
If used again, all the triggers associated with the stored relation are replaced.
To remove all triggers from a stored relation, use ``::set_triggers <REL_NAME>`` followed by nothing.

As an example of using triggers to maintain an index manually, suppose we have the following relation::

    :create rel {a => b}

and the manual index is::

    :create rel.rev {b, a}

To manage the manual index automatically::

    ::set_triggers rel

    on put {
        ?[a, b] := _new[a, b]

        :put rel.rev{ b, a }
    }
    on rm {
        ?[a, b] := _old[a, b]

        :rm rel.rev{ b, a }
    }

With the index set up, you can use ``*rel.rev{..}`` in place of ``*rel{..}`` in your queries.

Note that unlike indices, there are ingestion APIs for which triggers are explicitly *not* run. 
Also, if you want to manually manage indices with triggers, you have to populate the existing values
manually as well.

.. WARNING::

    Triggers do not propagate. That is, if a trigger modifies a relation that has triggers associated, 
    those latter triggers will not run. This is different from the behaviour in earlier versions.
    We changed it since trigger propagation creates more problems than it solves.

---------------------
Storing large values
---------------------

There a limit to the amount of data you can store in a single value or single row. The precise limit depends on the storage engine. For the in-memory engine it is obviously RAM-bound. For the SQLite engine the keys as as whole and the values as a whole are each stored as a single BLOB field in SQLite, and are subject to `their limit <https://www.sqlite.org/limits.html>`_. For RocksDB engine, which is the recommended setup if you are thinking of storing large values, the keys as a whole is stored as a RocksDB key, which has a limit of 8MB, and keys should be kept small for performance. For values, CozoDB utilizes the `BlobDB <https://github.com/facebook/rocksdb/wiki/BlobDB>`_ functionality of RocksDB, and you are only limited by RAM and disk sizes.

Performance-wise, if large values are present, currently these values will be read into memory if the row is touched in the query. So it is recommended to store large values in a dedicated key-value relation in the database, with all the metadata stored in a separate relation. At query time, you should search/filter/join the metadata relation to find the rows you want, and then join them with the dedicated large value relation at the last stage.
