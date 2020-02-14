import sublime_plugin
import sublime
# from GranularSubword import granular_move_pt

from sublime import Region


def copy_regions(view):
    regions = view.sel()
    return list(regions), regions


def change_selection_endpoints(view, begin):
    new_sel = []
    for sel in view.sel():
        reverse = (sel.a < sel.b) if begin else (sel.b < sel.a)
        new_sel.append(Region(sel.b, sel.a) if reverse else sel)
    view.sel().clear()
    view.sel().add_all(new_sel)


class TunnelingChangeSelectionEndpointCommand(sublime_plugin.TextCommand):
    def run(self, edit, begin):
        change_selection_endpoints(self.view, begin)


class TunnelingDeleteLeftFromSelectionEndCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        copy, regions = copy_regions(view)
        for c in reversed(copy):
            if c.size() > 0:
                regions.add(Region(c.begin(), c.end() - 1))
                view.erase(edit, Region(c.end() - 1, c.end()))


class TunnelingDeleteRightFromSelectionStartCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        copy, regions = copy_regions(view)
        for c in reversed(copy):
            if c.size() > 0:
                regions.add(Region(c.end(), c.begin() + 1))
                view.erase(edit, Region(c.begin(), c.begin() + 1))


def original_sublime_move_pt_by_subword(view, pt, forward):
    regions = view.sel()

    assert len(regions) == 0

    regions.add(Region(pt))
    by = "subword_ends" if forward else "subwords"
    view.run_command("move", {"forward": forward, "by": by})

    assert len(regions) == 1
    assert regions[0].size() == 0

    to_return = regions[0].a
    regions.clear()
    return to_return


class TunnelingDeleteSubwordLeftFromSelectionEndCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        copy, regions = copy_regions(view)
        regions.clear()

        for c in reversed(copy):
            if c.size() > 0:
                if len(sublime.find_resources("GranularSubword.py")) > 0:
                    from GranularSubword.GranularSubword import granular_move_pt
                    new_pt = granular_move_pt(view, c.end(), 'subword', forward=False)

                else:
                    new_pt = original_sublime_move_pt_by_subword(view, c.end(), False)

                new_pt = max(c.begin(), new_pt)
                assert new_pt < c.end()
                view.erase(edit, Region(new_pt, c.end()))
                regions.add(Region(c.begin(), new_pt))


class TunnelingDeleteSubwordRightFromSelectionStartCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        copy, regions = copy_regions(view)
        regions.clear()

        for c in reversed(copy):
            if c.size() > 0:
                if len(sublime.find_resources("GranularSubword.py")) > 0:
                    from GranularSubword.GranularSubword import granular_move_pt
                    new_pt = granular_move_pt(view, c.begin(), 'subword', forward=True)

                else:
                    new_pt = original_sublime_move_pt_by_subword(view, c.begin(), True)

                new_pt = min(new_pt, c.end())
                assert new_pt > c.begin()
                regions.add(Region(c.end(), new_pt))
                view.erase(edit, Region(c.begin(), new_pt))


class TunnelingClearSelectionsCommand(sublime_plugin.TextCommand):
    def run(self, edit, where):
        assert where in ['begin', 'end']
        copy, regions = copy_regions(self.view)
        regions.clear()
        for c in copy:
            if where == "begin":
                regions.add(Region(c.begin()))

            else:
                regions.add(Region(c.end()))


class AllSelectionsNonemptyContextListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key != "g_t_all_selections_nonempty":
            return None
        return all(r.size() > 0 for r in view.sel())


class ExistsCaretAtEndOfSelectionContextListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key != "g_t_exists_caret_at_end_of_selection":
            return None
        exists = any(s.a < s.b for s in view.sel())
        return exists == operand if operator == sublime.OP_EQUAL else exists != operand


class ExistsCaretAtBeginningOfSelectionContextListener(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key != "g_t_exists_caret_at_beginning_of_selection":
            return None
        exists = any(s.a > s.b for s in view.sel())
        return exists == operand if operator == sublime.OP_EQUAL else exists != operand
