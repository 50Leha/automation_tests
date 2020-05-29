Feature: Notepad`s tests

  Scenario: run a test of standard Notepad
     Given we open file in Notepad
      When we add some text in the Notepad file
      and kill the Notepad application
      Then we open Notepad file and text presents in it


  Scenario: run a test of Notepad++
     Given we open file in Notepad++
      When we add some text in the Notepad++ file
      and kill the Notepad++ application
      Then we open Notepadd++ file and text presents in it

