package com.careerbuilder.search.relevancy.Model;

import com.careerbuilder.search.relevancy.model.KnowledgeGraphRequest;
import com.google.gson.Gson;
import org.junit.Assert;
import org.junit.Test;

public class KnowledgeGraphRequestTest {

    private KnowledgeGraphRequest parse(String json) {
        return new Gson().fromJson(json, KnowledgeGraphRequest.class);
    }

    @Test
    public void defaults()
    {
        KnowledgeGraphRequest actual = parse("{\"queries\":[\"content:test\"]}");

        Assert.assertTrue(actual.normalize);
        Assert.assertTrue(actual.return_popularity);
        Assert.assertEquals(1, actual.min_popularity, 0);
    }

    @Test
    public void normalizeValues()
    {
        KnowledgeGraphRequest actual = parse("{\"queries\":[\"content:test\"],\"normalize_values\":false}");

        Assert.assertFalse(actual.normalize);
    }

    @Test
    public void normalizeAlias()
    {
        KnowledgeGraphRequest actual = parse("{\"queries\":[\"content:test\"],\"normalize\":false}");

        Assert.assertFalse(actual.normalize);
    }
}
