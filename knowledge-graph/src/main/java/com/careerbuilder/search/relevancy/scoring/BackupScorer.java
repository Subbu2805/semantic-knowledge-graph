package com.careerbuilder.search.relevancy.scoring;

import com.careerbuilder.search.relevancy.NodeContext;
import com.careerbuilder.search.relevancy.model.ResponseNode;
import com.careerbuilder.search.relevancy.waitable.QueryWaitable;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;

public class BackupScorer
{
    public void runFallback(NodeContext context,
                             ResponseNode response,
                             List<QueryWaitable> qRunners,
                             String fallbackField) {
        List<QueryWaitable> fgQueryWaitables = qRunners.stream().filter(q -> q.type == QueryWaitable.QueryType.FG).collect(Collectors.toList());
        HashSet<Integer> fallbackIndices = getFallbackIndices(fgQueryWaitables, context.request.min_popularity);
        QueryRunnerFactory factory = new QueryRunnerFactory(context, response, fallbackIndices);
        List<QueryWaitable> fallbackRunners = new LinkedList<>();
        fallbackRunners.addAll(factory.getQueryRunners(context.fgDomain, fallbackField, QueryWaitable.QueryType.FG));
        fallbackRunners.addAll(factory.getQueryRunners(context.bgDomain, fallbackField, QueryWaitable.QueryType.BG));
        if(context.request.return_popularity)
        {
            fallbackRunners.addAll(factory.getQueryRunners(context.queryDomain, fallbackField, QueryWaitable.QueryType.Q));
        }
        NodeScorer.parallelQuery(fallbackRunners);
        replaceRunners(qRunners, fallbackRunners);
    }

    protected HashSet<Integer> getFallbackIndices(List<QueryWaitable> values, double minCount)
    {
        HashSet<Integer> indices = new HashSet<>();
        for(QueryWaitable runner : values)
        {
            if(runner.result < minCount || runner.result == 0) {
                indices.add(runner.index);
            }
        }
        return indices;
    }

    protected void replaceRunners(List<QueryWaitable> target, List<QueryWaitable> replacers) {
        for(QueryWaitable replacer : replacers)
        {
            int index = target.indexOf(replacer);
            if(index < 0) {
                target.add(replacer);
            }
            else if(replacer.result > target.get(index).result) {
                target.set(index, replacer);
            }
        }
    }
}
