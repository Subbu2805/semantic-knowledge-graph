package com.careerbuilder.search.relevancy.utility;

import org.junit.Test;

import static junit.framework.TestCase.assertEquals;

public class ParseUtilityTest {

    @Test
    public void buildFieldQuery_phrase()
    {
        assertEquals("jobtitle:\"data scientist\"", ParseUtility.buildFieldQuery("jobtitle", "data scientist"));
    }

    @Test
    public void buildFieldQuery_escapesQuotesAndBackslashes()
    {
        assertEquals("skills:\"c\\\\c++ \\\"dev\\\"\"", ParseUtility.buildFieldQuery("skills", "c\\c++ \"dev\""));
    }

    @Test
    public void buildFieldQuery_nullOrBlankMatchesAll()
    {
        assertEquals("jobtitle:*", ParseUtility.buildFieldQuery("jobtitle", null));
        assertEquals("jobtitle:*", ParseUtility.buildFieldQuery("jobtitle", ""));
        assertEquals("jobtitle:*", ParseUtility.buildFieldQuery("jobtitle", "  "));
    }
}
