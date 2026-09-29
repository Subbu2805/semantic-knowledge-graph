package com.careerbuilder.search.relevancy.responsewriter;

import com.careerbuilder.search.relevancy.model.*;
import com.careerbuilder.search.relevancy.model.Error;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import org.apache.solr.common.SolrException;
import org.apache.solr.common.util.NamedList;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.response.QueryResponseWriter;
import org.apache.solr.response.SolrQueryResponse;

import java.io.IOException;
import java.io.Writer;

public class KnowledgeGraphResponseWriter implements QueryResponseWriter{

    public void init(NamedList args)
    {

    }
    public String getContentType(SolrQueryRequest request, SolrQueryResponse response)
    {
        return "application/json";
    }

    public void write(Writer writer, SolrQueryRequest request, SolrQueryResponse response) throws IOException
    {
        Gson gson = new GsonBuilder().registerTypeAdapter(ResponseValue.class, new ResponseValueSerializer()).create();
        Exception e = response.getException();
        int status = getStatus(response);
        KnowledgeGraphResponse model = (KnowledgeGraphResponse)response.getValues().get("relatednessResponse");
        if(e != null) {
            if(model == null) {
                model = new KnowledgeGraphResponse();
            }
            model.error = new Error(e.getMessage(), status);
        }
        writer.write(gson.toJson(model, KnowledgeGraphResponse.class));
    }

    private int getStatus(SolrQueryResponse response)
    {
        NamedList<Object> header = response.getResponseHeader();
        Object status = header == null ? null : header.get("status");
        if(status instanceof Number) {
            return ((Number) status).intValue();
        }
        return response.getException() == null ? 0 : SolrException.ErrorCode.SERVER_ERROR.code;
    }

}
