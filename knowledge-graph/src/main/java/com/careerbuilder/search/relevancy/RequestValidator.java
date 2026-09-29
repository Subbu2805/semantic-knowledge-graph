package com.careerbuilder.search.relevancy;

import com.careerbuilder.search.relevancy.model.KnowledgeGraphRequest;
import com.careerbuilder.search.relevancy.model.RequestNode;
import org.apache.solr.common.SolrException;
import org.apache.solr.request.SolrQueryRequest;

public class RequestValidator {

    private KnowledgeGraphRequest request;
    private SolrQueryRequest solrRequest;

    public RequestValidator(SolrQueryRequest solrRequest, KnowledgeGraphRequest request)
    {
        this.request = request;
        this.solrRequest= solrRequest;
    }

    public void validate()
    {
        if(request.queries == null || request.queries.length == 0) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "No queries supplied for generation / scoring");
        }
        if(request.compare == null || request.compare.length == 0) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "Request contains no compare node or an empty compare node");
        }
        if(request.min_popularity < 0) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "min_popularity must not be negative.");
        }
        for(int i = 0; i < request.compare.length; ++i) {
            recurse(request.compare[i]);
        }
    }

    private void recurse(RequestNode requestNode)
    {
        if(requestNode.type == null || requestNode.type.equals("")) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST, "A request node contains empty or null type.");
        }
        FieldChecker.checkField(solrRequest, requestNode.type, requestNode.type);

        if(requestNode.limit < 0) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST,
                    "A request node of type \"" + requestNode.type + "\" contains a negative limit.");
        }
        if(requestNode.min_popularity != null && requestNode.min_popularity < 0) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST,
                    "A request node of type \"" + requestNode.type + "\" contains a negative min_popularity.");
        }
        if(requestNode.values != null) {
            for (String value : requestNode.values) {
                if (value == null) {
                    throw new SolrException(SolrException.ErrorCode.BAD_REQUEST,
                            "A request node of type \"" + requestNode.type + "\" contains a null value.");
                }
            }
        }

        if(requestNode.compare != null) {
            for (int i = 0; i < requestNode.compare.length; ++i){
                recurse(requestNode.compare[i]);
            }
        }
    }
}
