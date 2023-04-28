==============================
Vector search
==============================

Cozo supports vector proximity search using the HNSW (Hierarchical Navigable Small World) algorithm. 

To use vector search, you first need to have a stored relation with vectors inside, for example::

    :create table {k: String => v: <F32; 128>}


Next you create a HNSW index on a table containing vectors. You use the following system operator to create the index::

    ::hnsw create table:index_name {
        dim: 128,
        m: 50,
        dtype: F32,
        fields: [v],
        distance: L2,
        ef_construction: 20,
        filter: k != 'foo',
        extend_candidates: false,
        keep_pruned_connections: false,
    }

The dimension ``dim`` and the data type ``dtype`` (defaults to F32) has to match the dimensions of any vector you index. The ``fields`` parameter is a list of fields in the table that should be indexed. The indexed fields must only contain vectors of the same dimension and data type, or ``null``, or a list of vectors of the same dimension and data type.

The ``distance`` parameter is the distance metric to use: the options are ``L2`` (default), ``Cosine`` and ``IP``. The ``m`` controls the maximal number of outgoing connections from each node in the graph, and the ``ef_construction`` parameter is the number of nearest neighbors to use when building the index: see the HNSW paper for details. The ``filter`` parameter, when given, are bound to the fields of the original relation and only those rows for which the expression evaluates to ``true`` are indexed. The ``extend_candidates`` parameter is a boolean (default false) that controls whether the index should extend the candidate list with the nearest neighbors of the nearest neighbors. The ``keep_pruned_connections`` parameter is a boolean (default false) that controls whether the index should keep pruned connections.

You can insert data as normally done into ``table``. For vectors, use a list of numbers and it will be verified to have the correct dimension and converted. If you want to be more explicit, you can use the ``vec`` function.

After the index is created, you can use vector search inside normal queries in a similar manner to stored relations. For example::

    ?[dist, k, v] := ~a:vec{ k, v | 
            query: q, 
            k: 2, 
            ef: 20, 
            bind_distance: dist, 
            bind_vector: bv, 
            bind_field: f, 
            bind_field_idx: fi, 
            filter: 1 + 1 == 2,
            radius: 0.1
        }, q = vec([200, 34])

The ``~`` followed by the index name signifies a vector search. In the braces, arguments before the vertical line are named bindings, with exactly the same semantics as in normal stored relations with named fields (i.e. they may be bound, or if they are unbound, the introduce fresh variables), and arguments after the vertical line are query parameters.

There are three required parameters: ``query`` is an expression that evaluates to a query vector of the expected type, and if it evaluates to a variable, the variable must be bound inside the rule; ``k`` controls how many results to return, and ``ef`` controls the number of neighbours to consider during the search process.

Next, there are three bind parameters that can bind variables to data that are only available in index or during the search process: ``distance`` binds the distance between the query vector and the result vector; ``vector`` binds the result vector; and ``field`` binds the field name of the result vector. The ``field_idx`` parameter binds the index of the field in the ``fields`` list of the index in case ``field`` resolves to a list of vectors, otherwise it is ``null``. In case any of the bind parameters are bound to existing variables, they act as filters after ``k`` results are returned.

The parameter ``filter`` takes an expression that can only refer to the fields of the original relation, and only those rows for which the expression evaluates to ``true`` are returned, and this filtering results occurs during the search process, so the algorithm will strive to return ``k`` results even if it must filter out a larger number of rows. ``radius`` controls the largest distance any return vector can have from the query vector, and this filtering process also happens during the search.

The vector search can be used in any place where a stored relation may be used, even inside recursive rules (but be careful of non-termination).

As with normal indices, you can use the index relation as a read-only but otherwise normal relation in your query. You query the index directly by::

    ?[fr_k, to_k, dist] := *table:index_name {layer: 0, fr_k, to_k, dist}

It is recommended to always specify ``layer``, otherwise a full scan is required.

The schema for the above index is the following::

    {
        layer: Int,
        fr_k: String?,
        fr__field: Int?,
        fr__field_idx: Int?,
        to_k: String?,
        to__field: Int?,
        to__field_idx: Int?,
        => 
        dist: Float,
        hash: Bytes,
        ignore_link: Bool,
    }

Layer is the layer in the HNSW hierarchy of graphs, with ``0`` the most detailed layer, ``-1`` the layer more abstract than ``0``, ``-2`` the even more abstract layer, etc. There is also a special layer ``1`` containing at most one row with all other keys set to null.

The ``fr_*`` and ``to_*`` fields mirror the indices of the indexed relation, and the ``fr__*`` and ``to__*`` fields indicate which vectors inside the original rows this edge connects.

``dist`` is the distance between the two vectors when the row represents a link between two different vectors, otherwise the link is a self-loop and ``dist`` contains the degree of the node; ``hash`` is the hash of the vector, and ``ignore_link`` is a boolean that indicates whether this link should be ignored during the search process. The graph is guaranteed to be symmetric, but the incoming and outgoing links may have different ``ignore_link`` values, and they cannot both be ``true``.

Walking the index graph at layer 0 amounts to probabilistically visiting "near" neigbours. More abstract layers are renormalized versions of the proximity graph and are harder to work with but are even more interesting theoretically.

To drop an HNSW index::

    ::hnsw drop table:index_name
