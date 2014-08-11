"""

    DirBuster does not provide ranking for the vulnerabilities it has found.
    This file tries to define a ranking for every DirBuster's discoveries it
    might find.

"""


from framework.lib.libptp.constants import HIGH, MEDIUM, LOW, INFO


# TODO: Complete the signatures database.
DIRECTORIES = {
    r'.*/admin/': INFO,
}


FILES = {
    r'.*/config\.php.*': HIGH,
}
