package com.careerbuilder.search.relevancy.utility;

import com.careerbuilder.search.relevancy.model.*;

import java.util.*;
import java.util.stream.Collectors;

public class ResponseUtility {

    // keeps all passed in values, up to request.limit
    // keeps as many generated values as possible up to request.limit
    public static ResponseValue[] filterAndSortValues(ResponseValue [] responses, RequestNode node, KnowledgeGraphRequest request) {
        List<ResponseValue> scoredValues = new ArrayList<>(Arrays.asList(responses));
        SortUtility.sortResponseValues(scoredValues, node.sort);

        double minPopularity = minPopularity(node, request);
        if (request.return_popularity)
        {
            scoredValues = thresholdMinPop(scoredValues, minPopularity);
        }
        else
        {
            scoredValues = thresholdMinFGBGPop(scoredValues, minPopularity);
        }
        distinct(scoredValues);
        if(scoredValues.size() > 0) {
            List<String> requestValues = retainScored(distinct(node.values), scoredValues);
            int limit = Math.min(scoredValues.size(), node.limit);
            scoredValues = filterMergeResults(scoredValues, requestValues, limit, node.sort);
        }
        return scoredValues.toArray(new ResponseValue[scoredValues.size()]);
    }

    protected static double minPopularity(RequestNode node, KnowledgeGraphRequest request)
    {
        return node.min_popularity == null ? request.min_popularity : node.min_popularity;
    }

    // passed-in values which fell below the popularity threshold are no longer scored, so they cannot be kept
    protected static List<String> retainScored(List<String> requestValues, List<ResponseValue> scoredValues)
    {
        return requestValues.stream().filter(
                (String s) -> scoredValues.stream().anyMatch(r -> r.valuesEqual(new ResponseValue(s))))
                .collect(Collectors.toCollection(LinkedList::new));
    }

    protected static List<ResponseValue> thresholdMinPop(List<ResponseValue> values, double threshold)
    {
        values = values.stream().filter((ResponseValue r) ->
                (r.popularity >= threshold)).collect(Collectors.toList());
        return thresholdMinFGBGPop(values, threshold);
    }

    protected static List<ResponseValue> thresholdMinFGBGPop(List<ResponseValue> values, double threshold) {
        return values.stream().filter((ResponseValue r) -> (r.background_popularity >= threshold
                        && r.foreground_popularity >= threshold)).collect(Collectors.toList());
    }

    protected static List<String> distinct(String [] requestValues )
    {
        return new LinkedList<>(
                (Arrays.stream(requestValues == null ? new String[0] : requestValues).collect(
                        Collectors.toMap(String::toLowerCase, s -> s, (first, second) -> first))
                        .values()));
    }

    public static void distinct(List<ResponseValue> responseValues)
    {
        for(int i = 1; i < responseValues.size();) {
            if(responseValues.get(i).expandedEquals(responseValues.get(i-1))) {
                responseValues.remove(i-1);
            }
            else { ++i; }
        }
    }

    // move any keep values (request values) beyond the request limit to just within the request limit, replacing generated values
    public static List<ResponseValue> filterMergeResults(List<ResponseValue> results,
                                                         List<String> requestValues, int limit, SortType sort)
    {
        List<String> keepSet = requestValues == null ? new LinkedList<>() : requestValues;
        if (keepSet.size() > results.size())
            throw new IllegalArgumentException("The keep set is larger than the results set.");

        List<ResponseValue> keepList= new LinkedList<>();
        List<ResponseValue> disposableList = new LinkedList<>();
        for (ResponseValue r : results)
        {
            if (keepSet.stream().anyMatch(s -> r.valuesEqual(new ResponseValue(s))))
                keepList.add(r);
            else
                disposableList.add(r);
        }

        if (keepList.size() < limit)
        {
            int numResultsToAdd = Math.min(limit - keepList.size(), disposableList.size());
            keepList.addAll(disposableList.subList(0, numResultsToAdd));
        }
        SortUtility.sortResponseValues(keepList, sort);
        return keepList;
    }
}
