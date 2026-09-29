package com.careerbuilder.search.relevancy.utility;

import org.apache.lucene.search.MatchAllDocsQuery;
import org.apache.lucene.search.Query;
import org.apache.solr.common.SolrException;
import org.apache.solr.request.SolrQueryRequest;
import org.apache.solr.search.QParser;
import org.apache.solr.search.SyntaxError;

import java.util.LinkedList;
import java.util.List;

public class ParseUtility
{
    public static List<Query> parseQueryStrings(String [] qStrings, SolrQueryRequest req) {
        if(qStrings != null) {
            LinkedList<Query> queryList = new LinkedList<Query>();
            for (String qString : qStrings) {
                queryList.add(parseQueryString(qString, req));
            }
            return queryList;
        }
        List<Query> deflt = new LinkedList<>();
        deflt.add(new MatchAllDocsQuery());
        return deflt;
    }

    // builds a phrase query against a single field, e.g. jobtitle:"data scientist"
    public static String buildFieldQuery(String field, String value) {
        if(value == null || value.trim().equals("")) {
            return field + ":*";
        }
        return field + ":\"" + escapeQueryValue(value) + "\"";
    }

    public static String escapeQueryValue(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    public static Query parseQueryString(String qString, SolrQueryRequest req) {
        try {
            QParser parser = QParser.getParser(qString, req.getParams().get("defType"), req);
            return parser.getQuery();
        } catch (SyntaxError e) {
            throw new SolrException(SolrException.ErrorCode.BAD_REQUEST,
                    "Syntax error in query: " + qString + ".");
        }
    }
}
