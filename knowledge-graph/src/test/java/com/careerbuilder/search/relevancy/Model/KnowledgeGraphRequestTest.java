package com.careerbuilder.search.relevancy.Model;

import com.careerbuilder.search.relevancy.model.KnowledgeGraphRequest;
import com.google.gson.Gson;
import org.junit.Assert;
import org.junit.Test;

import static junit.framework.TestCase.assertFalse;
import static junit.framework.TestCase.assertNull;
import static junit.framework.TestCase.assertTrue;

public class KnowledgeGraphRequestTest {

    private KnowledgeGraphRequest parse(String json)
    {
        return new Gson().fromJson(json, KnowledgeGraphRequest.class);
    }

    @Test
    public void normalizeValuesDefaultsToTrue()
    {
        assertTrue(parse("{\"queries\":[\"*:*\"]}").normalize);
    }

    @Test
    public void normalizeValuesIsHonored()
    {
        assertFalse(parse("{\"normalize_values\": false}").normalize);
    }

    @Test
    public void normalizeRemainsSupported()
    {
        assertFalse(parse("{\"normalize\": false}").normalize);
    }

    @Test
    public void nodeMinPopularityIsOptional()
    {
        KnowledgeGraphRequest inherited = parse("{\"compare\":[{\"type\":\"skills\"}]}");
        assertNull(inherited.compare[0].min_popularity);

        KnowledgeGraphRequest overridden = parse("{\"compare\":[{\"type\":\"skills\",\"min_popularity\":5}]}");
        Assert.assertEquals(Double.valueOf(5.0), overridden.compare[0].min_popularity);
    }
}
